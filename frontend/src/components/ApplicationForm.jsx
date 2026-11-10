import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { api, errorMessage } from '../services/api'
import { useApiMutation, usePlatforms } from '../hooks/useData'
import { EMPLOYMENT_TYPES, STATUSES } from '../utils/constants'
import { todayISO } from '../utils/format'
import { ErrorNote, Field, Modal } from './ui'

const url = z.string().trim().refine((v) => !v || /^https?:\/\/\S+$/i.test(v), 'Enter a full link starting with http:// or https://')
const schema = z.object({
  job_title: z.string().trim().min(1, 'Enter the job title'),
  company_name: z.string().trim().min(1, 'Enter the company name'),
  platform_id: z.coerce.number({ invalid_type_error: 'Choose a platform' }).int().positive('Choose a platform'),
  application_date: z.string().min(1, 'Choose the application date'),
  status: z.enum(STATUSES.map((s) => s.value)),
  employment_type: z.string().optional(),
  location: z.string().optional(),
  salary_range: z.string().optional(),
  job_url: url,
  company_website: url,
  contact_person: z.string().optional(),
  job_description: z.string().optional(),
  notes: z.string().optional(),
})

const blank = (a) => ({
  job_title: a?.job_title ?? '', company_name: a?.company_name ?? '', platform_id: a?.platform_id ?? '',
  application_date: a?.application_date ?? todayISO(), status: a?.status ?? 'applied', employment_type: a?.employment_type ?? '',
  location: a?.location ?? '', salary_range: a?.salary_range ?? '', job_url: a?.job_url ?? '', company_website: a?.company_website ?? '',
  contact_person: a?.contact_person ?? '', job_description: a?.job_description ?? '', notes: a?.notes ?? '',
})

export default function ApplicationForm({ application, onClose, onSaved }) {
  const { data: platforms = [] } = usePlatforms()
  const [newPlatform, setNewPlatform] = useState('')
  const [platformError, setPlatformError] = useState('')
  const { register, handleSubmit, setValue, formState: { errors } } = useForm({ resolver: zodResolver(schema), defaultValues: blank(application) })

  const save = useApiMutation(
    (values) => {
      const body = { ...values, employment_type: values.employment_type || null }
      return (application ? api.put(`/applications/${application.id}`, body) : api.post('/applications', body)).then((r) => r.data)
    },
    { onSuccess: (saved) => { onSaved?.(saved); onClose() } },
  )
  const addPlatform = useApiMutation((name) => api.post('/platforms', { name }).then((r) => r.data), {
    refresh: false,
    onSuccess: (p) => { setNewPlatform(''); setPlatformError(''); setTimeout(() => setValue('platform_id', p.id, { shouldValidate: true }), 50) },
  })

  return (
    <Modal title={application ? 'Edit application' : 'Add application'} onClose={onClose} wide>
      <form onSubmit={handleSubmit((v) => save.mutate(v))} className="grid grid-cols-1 gap-4 sm:grid-cols-2" noValidate>
        <Field label="Job title" error={errors.job_title?.message}><input {...register('job_title')} placeholder="Backend Developer" /></Field>
        <Field label="Company" error={errors.company_name?.message}><input {...register('company_name')} placeholder="ABC Technologies" /></Field>
        <Field label="Platform" error={errors.platform_id?.message}>
          <select {...register('platform_id')}>
            <option value="">Choose a platform</option>
            {platforms.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </Field>
        <Field label="Status" error={errors.status?.message}>
          <select {...register('status')}>{STATUSES.map((s) => <option key={s.value} value={s.value}>{s.label}</option>)}</select>
        </Field>
        <Field label="Application date" error={errors.application_date?.message} hint="For saved jobs, use the day you saved it.">
          <input type="date" {...register('application_date')} />
        </Field>
        <Field label="Employment type">
          <select {...register('employment_type')}><option value="">Not specified</option>{EMPLOYMENT_TYPES.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}</select>
        </Field>
        <div className="sm:col-span-2">
          <div className="flex items-end gap-2">
            <Field label="Can't find your platform? Add one" className="flex-1"><input value={newPlatform} onChange={(e) => setNewPlatform(e.target.value)} placeholder="Wellfound" /></Field>
            <button type="button" className="btn btn-secondary" disabled={!newPlatform.trim() || addPlatform.isPending}
              onClick={() => addPlatform.mutate(newPlatform.trim(), { onError: (e) => setPlatformError(errorMessage(e)) })}>Add platform</button>
          </div>
          {platformError && <p role="alert" className="mt-1 text-xs text-rose-600 dark:text-rose-400">{platformError}</p>}
        </div>
        <Field label="Job link" error={errors.job_url?.message}><input {...register('job_url')} placeholder="https://" inputMode="url" /></Field>
        <Field label="Company website" error={errors.company_website?.message}><input {...register('company_website')} placeholder="https://" inputMode="url" /></Field>
        <Field label="Location"><input {...register('location')} placeholder="Lahore, remote" /></Field>
        <Field label="Salary range"><input {...register('salary_range')} placeholder="PKR 250k–350k" /></Field>
        <Field label="Contact person" className="sm:col-span-2"><input {...register('contact_person')} placeholder="Name of the recruiter or hiring manager" /></Field>
        <Field label="Job description" className="sm:col-span-2"><textarea {...register('job_description')} /></Field>
        <Field label="Notes" className="sm:col-span-2"><textarea {...register('notes')} /></Field>
        <div className="sm:col-span-2">
          <ErrorNote>{save.isError ? errorMessage(save.error) : ''}</ErrorNote>
          <div className="mt-2 flex justify-end gap-2">
            <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
            <button className="btn btn-primary" disabled={save.isPending}>{save.isPending ? 'Saving…' : application ? 'Save changes' : 'Add application'}</button>
          </div>
        </div>
      </form>
    </Modal>
  )
}
