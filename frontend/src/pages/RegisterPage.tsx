import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuth } from '../hooks/useAuth';
import { Link, useNavigate } from 'react-router-dom';
import { Input, Label } from '../components/ui/Input';
import { Button } from '../components/ui/Button';
import { Alert } from '../components/ui/Alert';
import { Select } from '../components/ui/Select';

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  full_name: z.string().min(2),
  role: z.enum(['PATIENT', 'CAREGIVER', 'CLINICIAN', 'ADMIN']),
});

type RegisterForm = z.infer<typeof registerSchema>;

export const RegisterPage: React.FC = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = React.useState('');

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
    defaultValues: { role: 'CLINICIAN' }
  });

  const onSubmit = async (data: RegisterForm) => {
    try {
      await registerUser(data);
      navigate('/app');
    } catch (err) {
      setError('Registration failed');
    }
  };

  return (
    <div className="space-y-6">
      {error && <Alert variant="error">{error}</Alert>}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <Label htmlFor="full_name">Full Name</Label>
          <Input id="full_name" {...register('full_name')} error={errors.full_name?.message} />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...register('email')} error={errors.email?.message} />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" {...register('password')} error={errors.password?.message} />
        </div>
        <div>
          <Label htmlFor="role">Role</Label>
          <Select 
            id="role" 
            {...register('role')} 
            error={errors.role?.message}
            options={[
              { value: 'CLINICIAN', label: 'Clinician' },
              { value: 'PATIENT', label: 'Patient' },
              { value: 'CAREGIVER', label: 'Caregiver' },
              { value: 'ADMIN', label: 'Researcher / Admin' },
            ]}
          />
        </div>
        <Button type="submit" className="w-full" isLoading={isSubmitting}>Register</Button>
      </form>
      <div className="text-center text-sm">
        Already have an account? <Link to="/login" className="text-primary-600 hover:underline">Log in</Link>
      </div>
    </div>
  );
};
