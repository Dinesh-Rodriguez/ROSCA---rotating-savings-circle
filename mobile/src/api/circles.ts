import { apiFetch } from './client';

export type MemberStatus = 'recipient' | 'contributed' | 'waiting';

export type Membership = {
  id: number;
  user_id: number;
  username: string;
  position: number;
  paid_out: boolean;
};

export type RoundMemberStatus = {
  membership_id: number;
  status: MemberStatus;
};

export type RoundStatus = 'OPEN' | 'PENDING_APPROVAL' | 'CLOSED';

export type Round = {
  id: number;
  round_number: number;
  status: RoundStatus;
  deadline: string;
  recipient: number;
  final_payout_amount: number | null;
  approved_at: string | null;
  member_statuses: RoundMemberStatus[];
};

export type Circle = {
  id: number;
  name: string;
  invite_code: string;
  contribution_amount: number;
  penalty_rate: number;
  created_at: string;
  admin: number;
  members: Membership[];
  current_round: Round | null;
};

export function fetchCircle(circleId: string | number): Promise<Circle> {
  return apiFetch<Circle>(`circles/${circleId}/`);
}

export function contributeToRound(roundId: number): Promise<unknown> {
  return apiFetch(`rounds/${roundId}/contribute/`, { method: 'POST' });
}

export function approveRound(roundId: number): Promise<unknown> {
  return apiFetch(`rounds/${roundId}/approve/`, { method: 'POST' });
}
