import React, { useEffect, useState } from 'react';
import { View, Text, Button, Alert, ScrollView } from 'react-native';
import ApiService from './ApiService';  // Import your ApiService

const VoteScreen = () => {
  const [role, setRole] = useState('');
  const [choices, setChoices] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch current role and choices when the component is mounted
    const fetchRole = async () => {
      try {
        // Fetch current role from backend
        const currentRole = await ApiService.getCurrentRole();
        setRole(currentRole);

        // Fetch choices from the server (you can also fetch choices from a text file or another API endpoint)
        const response = await fetch('https://yourdomain.com/choices.txt');  // Adjust as needed
        const data = await response.text();
        setChoices(data.split('\n'));  // Assuming choices are separated by newline in the file

        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching role or choices:', error);
        setIsLoading(false);
      }
    };

    fetchRole();
  }, []);  // Empty dependency array means this will run once when the component mounts

  const handleVote = async (selectedName) => {
    try {
      // Submit the vote for the selected name
      const message = await ApiService.submitVote(selectedName);
      Alert.alert('Vote Submitted', message);
    } catch (error) {
      Alert.alert('Error', 'Failed to submit vote. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <View>
        <Text>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView>
      <View>
        <Text>Current Role: {role}</Text>
        {choices.map((choice, index) => (
          <Button
            key={index}
            title={`Vote for ${choice}`}
            onPress={() => handleVote(choice)}  // When a button is pressed, submit the vote
          />
        ))}
      </View>
    </ScrollView>
  );
};

export default VoteScreen;
