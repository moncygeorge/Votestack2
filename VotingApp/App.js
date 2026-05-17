import React, { useState, useEffect } from 'react';
import { View, Text, Button, TextInput, Alert } from 'react-native';
import axios from 'axios';

const App = () => {
  const [role, setRole] = useState('');
  const [name, setName] = useState('');

  // Fetch current role from the Flask backend
  useEffect(() => {
    axios.get('https://yourdomain.com/api/current_role')
      .then(response => {
        setRole(response.data.role);
      })
      .catch(error => {
        console.error(error);
        Alert.alert("Error", "Unable to fetch role.");
      });
  }, []);

  // Submit vote to the Flask backend
  const submitVote = () => {
    if (!name) {
      Alert.alert("Error", "Please select a name to vote for.");
      return;
    }

    axios.post('https://yourdomain.com/api/vote', { name })
      .then(response => {
        Alert.alert("Success", response.data.message);
      })
      .catch(error => {
        Alert.alert("Error", error.response.data.error);
      });
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 24, fontWeight: 'bold' }}>Current Role: {role}</Text>

      <TextInput
        style={{ height: 40, borderColor: 'gray', borderWidth: 1, marginTop: 20 }}
        placeholder="Enter your vote"
        value={name}
        onChangeText={setName}
      />

      <Button title="Submit Vote" onPress={submitVote} />
    </View>
  );
};

export default App;
