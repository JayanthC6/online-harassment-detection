export const apiClient = async (endpoint, options = {}) => {
  const token = localStorage.getItem('adminToken');
  
  const headers = {
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  // If we are passing FormData, do not set Content-Type to application/json
  if (options.body && typeof options.body === 'string' && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`/api${endpoint}`, config);
  let data;
  try {
    data = await response.json();
  } catch (e) {
    data = null;
  }

  if (!response.ok) {
    if (response.status === 401) {
      window.dispatchEvent(new Event('auth:unauthorized'));
    }
    const message = data?.error || data?.message || 'Request failed';
    throw new Error(message);
  }

  return data;
};
