import { API_URL } from '../api';

export interface Employee {
  id: number;
  account: {
    id: number;
    email: string;
  };
  date_of_birth: string;
  hire_date: string;
  phone_number: string;
  address: string;
  gender: string;
}

export const fetchEmployees = async (): Promise<Employee[]> => {
  const response = await fetch(`${API_URL}/employees/`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch employees');
  }

  return response.json();
};