export const login = async (email: string, password: string) => {
  const response = await fetch('http://localhost:8000/api/token/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    throw new Error('Invalid credentials');
  }

  const data = await response.json();
  const { access, refresh, role } = data;

  // Save tokens to localStorage
  localStorage.setItem('access_token', access);
  localStorage.setItem('refresh_token', refresh);

  return { access, refresh, role };
};

export const logout = () => {
  // Clear tokens from localStorage
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};