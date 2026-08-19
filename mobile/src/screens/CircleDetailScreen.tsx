import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, Button, StyleSheet, Text, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { ApiError } from '../api/client';
import { approveRound, contributeToRound, fetchCircle, MemberStatus, Membership, Round } from '../api/circles';
import { useAuth } from '../context/AuthContext';
import type { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'CircleDetail'>;

function statusLabel(status: MemberStatus): string {
  switch (status) {
    case 'recipient':
      return 'Recipient';
    case 'contributed':
      return 'Contributed';
    case 'waiting':
      return 'Waiting';
  }
}

export default function CircleDetailScreen({ route }: Props) {
  const { circleId } = route.params ?? {};
  const { session } = useAuth();

  const [members, setMembers] = useState<Membership[]>([]);
  const [round, setRound] = useState<Round | null>(null);
  const [adminId, setAdminId] = useState<number | null>(null);
  // Keyed by membership id, seeded from the fetched round on every load and
  // mutated directly by the optimistic Contribute flow between loads.
  const [statuses, setStatuses] = useState<Record<number, MemberStatus>>({});
  const [rowErrors, setRowErrors] = useState<Record<number, string>>({});
  const [rowSubmitting, setRowSubmitting] = useState<Record<number, boolean>>({});

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [approveError, setApproveError] = useState<string | null>(null);

  const loadCircle = useCallback(async () => {
    if (!circleId) {
      return;
    }
    setLoadError(null);
    try {
      const circle = await fetchCircle(circleId);
      setMembers(circle.members);
      setAdminId(circle.admin);
      setRound(circle.current_round);
      const nextStatuses: Record<number, MemberStatus> = {};
      circle.current_round?.member_statuses.forEach((entry) => {
        nextStatuses[entry.membership_id] = entry.status;
      });
      setStatuses(nextStatuses);
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : 'Failed to load this circle.');
    } finally {
      setLoading(false);
    }
  }, [circleId]);

  useEffect(() => {
    loadCircle();
  }, [loadCircle]);

  const handleContribute = async (membershipId: number) => {
    if (!round) {
      return;
    }
    const previousStatus = statuses[membershipId];

    // Optimistic update: flip the row to "contributed" immediately, before
    // the network call resolves.
    setStatuses((prev) => ({ ...prev, [membershipId]: 'contributed' }));
    setRowErrors((prev) => {
      const next = { ...prev };
      delete next[membershipId];
      return next;
    });
    setRowSubmitting((prev) => ({ ...prev, [membershipId]: true }));

    try {
      await contributeToRound(round.id);
      // Success: leave the optimistic value in place, and pick up any
      // knock-on change (e.g. round moving to PENDING_APPROVAL) in the background.
      loadCircle();
    } catch (err) {
      // Failure: roll the row back to what it was before the tap, and
      // surface the error right on that row.
      setStatuses((prev) => ({ ...prev, [membershipId]: previousStatus }));
      setRowErrors((prev) => ({
        ...prev,
        [membershipId]: err instanceof ApiError ? err.message : 'Failed to contribute.',
      }));
    } finally {
      setRowSubmitting((prev) => ({ ...prev, [membershipId]: false }));
    }
  };

  const handleApprove = async () => {
    if (!round) {
      return;
    }
    setApproveError(null);
    setApproving(true);
    try {
      await approveRound(round.id);
      await loadCircle();
    } catch (err) {
      setApproveError(err instanceof ApiError ? err.message : 'Failed to approve payout.');
    } finally {
      setApproving(false);
    }
  };

  if (!circleId) {
    return (
      <View style={styles.container}>
        <Text>No circle selected.</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator />
      </View>
    );
  }

  if (loadError) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>{loadError}</Text>
        <Button title="Retry" onPress={loadCircle} />
      </View>
    );
  }

  const isAdmin = session != null && adminId != null && session.userId === adminId;
  const canApprove = isAdmin && round?.status === 'PENDING_APPROVAL';

  return (
    <View style={styles.container}>
      {members.map((member) => {
        const status = statuses[member.id];
        const canContribute =
          round != null && round.status === 'OPEN' && status !== 'recipient' && status !== 'contributed';

        return (
          <View key={member.id} style={styles.row}>
            <Text>
              {member.username} (#{member.position}) — {status ? statusLabel(status) : '—'}
            </Text>
            {canContribute && (
              <Button
                title={rowSubmitting[member.id] ? 'Submitting...' : 'Contribute'}
                onPress={() => handleContribute(member.id)}
                disabled={rowSubmitting[member.id]}
              />
            )}
            {rowErrors[member.id] && <Text style={styles.error}>{rowErrors[member.id]}</Text>}
          </View>
        );
      })}

      {canApprove && (
        <View style={styles.approveSection}>
          <Button title={approving ? 'Approving...' : 'Approve Payout'} onPress={handleApprove} disabled={approving} />
          {approveError && <Text style={styles.error}>{approveError}</Text>}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  row: {
    marginBottom: 16,
  },
  approveSection: {
    marginTop: 16,
  },
  error: {
    color: 'red',
    marginTop: 4,
  },
});
