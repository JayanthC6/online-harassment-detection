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

  const predictText = (text, actorId, persist = true) => executePredict('/predict/instant', { text, actor_id: actorId, persist });
  
  const predictConversation = (messages, persist = true) => executePredict('/predict/conversation', { messages, persist });
  
  const predictAudio = (file, actorId, persist = true) => {
    const formData = new FormData();
    formData.append('file', file);
    if (actorId) formData.append('actor_id', actorId);
    formData.append('persist', persist);
    return executePredict('/predict/audio', formData, true);
  };
  
  const predictScreenshot = (file, actorId, platform = "generic", persist = true) => {
    const formData = new FormData();
    formData.append('file', file);
    if (actorId) formData.append('actor_id', actorId);
    formData.append('platform', platform);
    formData.append('persist', persist);
    return executePredict('/predict/screenshot', formData, true);
  };

  const importConversation = (file, persist = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('persist', persist);
    return executePredict('/predict/conversation/import', formData, true);
  };

  const predictFile = (file, actorId, persist = true) => {
    const formData = new FormData();
    formData.append('file', file);
    if (actorId) formData.append('actor_id', actorId);
    formData.append('persist', persist);
    return executePredict('/predict/file', formData, true);
  };

  const clearResult = () => {
    setResult(null);
    setError(null);
  };

  return { loading, error, result, predictText, predictConversation, importConversation, predictAudio, predictScreenshot, predictFile, clearResult };
}
