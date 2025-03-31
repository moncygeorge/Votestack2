import axios from 'axios';

const BASE_URL = 'https://yourdomain.com'; // Replace with your actual Flask backend URL

const ApiService = {
  // Fetch the current topic from the Flask backend
  getCurrentTopic: async () => {
    try {
      const response = await axios.get(`${BASE_URL}/api/current_topic`);
      return response.data.topic;  // Assuming your Flask response contains the topic
    } catch (error) {
      console.error('Error fetching current topic:', error);
      throw error;  // You can handle this error in the component
    }
  },

  // Submit a vote for a selected choice
  submitVote: async (selectedName) => {
    try {
      const response = await axios.post(`${BASE_URL}/api/submit_vote`, { name: selectedName });
      return response.data.message;  // Assuming your Flask response contains a success message
    } catch (error) {
      console.error('Error submitting vote:', error);
      throw error;  // You can handle this error in the component
    }
  }
};

export default ApiService;
