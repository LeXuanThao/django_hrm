import React, { useEffect, useState } from 'react';
import { fetchEmployees, Employee } from '../services/employeeService';
import EmployeeRow from '../components/EmployeeRow';

const EmployeeListPage: React.FC = () => {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const loadEmployees = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await fetchEmployees();
        setEmployees(data);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadEmployees();
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Employee List</h1>
      {error && <p className="text-error mb-4">{error}</p>}
      {loading ? (
        <div className="flex justify-center items-center">
          <span className="loading loading-spinner loading-lg"></span>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table table-zebra w-full">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Date of Birth</th>
                <th>Hire Date</th>
                <th>Phone Number</th>
                <th>Address</th>
                <th>Gender</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((employee) => (
                <EmployeeRow key={employee.id} employee={employee} />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default EmployeeListPage;