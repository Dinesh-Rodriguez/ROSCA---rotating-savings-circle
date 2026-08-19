import React, { useState } from 'react';
import { ActivityIndicator, Button, StyleSheet, Text, TextInput, View } from 'react-native';
import type { NativeStackScreenProps } from '@react-navigation/native-stack';
import { apiFetch, ApiError } from '../api/client';
import { useAuth } from '../context/AuthContext';
import type { RootStackParamList } from '../navigation/RootNavigator';

type Props = NativeStackScreenProps<RootStackParamList, 'Login'>;

type LoginResponse = {
  token: string;
  user_id: number;
  username: string;
};

export default function LoginScreen({ navigation }: Props) {
  const { setSession } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleLogin = async () => {
    setError(null);
    setSubmitting(true);
    try {
      const response = await apiFetch<LoginResponse>('auth/login/', {
        method: 'POST',
        body: { username, password },
      });
      setSession({ token: response.token, userId: response.user_id, username: response.username });
      navigation.replace('CircleDetail', {});
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Username</Text>
      <TextInput
        style={styles.input}
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
        autoCorrect={false}
      />

      <Text style={styles.label}>Password</Text>
      <TextInput
        style={styles.input}
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        autoCapitalize="none"
      />

      {error ? <Text style={styles.error}>{error}</Text> : null}

      {submitting ? (
        <ActivityIndicator />
      ) : (
        <Button title="Log In" onPress={handleLogin} disabled={!username || !password} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 16,
  },
  label: {
    marginBottom: 4,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 4,
    padding: 8,
    marginBottom: 16,
  },
  error: {
    color: 'red',
    marginBottom: 12,
  },
});
