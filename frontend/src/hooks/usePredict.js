import { useState } from 'react';
import { apiClient } from '../api/client';

export function usePredict() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const executePredict = async (endpoint, payload, isFormData = false) => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const options = {
        method: 'POST',
        body: isFormData ? payload : JSON.stringify(payload)
      };
      const data = await apiClient(endpoint, options);
      setResult(data);
      return data;
    } catch (err) {
      setError(err.message);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const predictText = (text, actorId) => executePredict('/predict', { text, actor_id: actorId });
  
  const predictConversation = (messages) => executePredict('/predict/conversation', { messages });
  
  const predictAudio = (file, actorId) => {
    const formData = new FormData();
    formData.append('file', file);
    if (actorId) formData.append('actor_id', actorId);
    return executePredict('/predict/audio', formData, true);
  };
  
  const predictScreenshot = (file, actorId, platform = "generic") => {
    const formData = new FormData();
    formData.append('file', file);
    if (actorId) formData.append('actor_id', actorId);
    formData.append('platform', platform);
    return executePredict('/predict/screenshot', formData, true);
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return { loading, error, result, predictText, predictConversation, predictAudio, predictScreenshot, clearResult };
}
