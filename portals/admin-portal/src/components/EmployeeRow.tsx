import React from 'react';
import { Employee } from '../services/employeeService';

interface EmployeeRowProps {
  employee: Employee;
}

const EmployeeRow: React.FC<EmployeeRowProps> = ({ employee }) => {
  return (
    <tr>
      <td>{employee.id}</td>
      <td>{employee.account.email}</td>
      <td>{employee.date_of_birth}</td>
      <td>{employee.hire_date}</td>
      <td>{employee.phone_number}</td>
      <td>{employee.address}</td>
      <td>{employee.gender}</td>
    </tr>
  );
};

export default EmployeeRow;