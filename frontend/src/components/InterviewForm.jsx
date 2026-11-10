import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { api, errorMessage } from '../services/api'
import { useApiMutation, useApplications } from '../hooks/useData'
import { toLocalInput } from '../utils/format'
import { ErrorNote, Field, Modal } from './ui'

const schema = z.object({
  application_id: z.coerce.number({ invalid_type_error: 'Choose an application' }).int().positive('Choose an application'),
  interview_date: z.string().min(1, 'Choose the date and time'),
  interview_type: z.string().optional(),
  meeting_link: z.string().trim().refine((v) => !v || /^https?:\/\/\S+$/i.test(v), 'Enter a full link starting with http:// or https://'),
  notes: z.string().optional(),
})

export default function InterviewForm({ interview, applicationId, onClose }) {
  const { data } = useApplications({ sort: 'updated', page_size: 200 })
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
    defaultValues: {
      application_id: interview?.application_id ?? applicationId ?? '', interview_date: interview ? toLocalInput(interview.interview_date) : '',
      interview_type: interview?.interview_type ?? '', meeting_link: interview?.meeting_link ?? '', notes: interview?.notes ?? '',
    },
  })
  const save = useApiMutation((v) => {
    const body = { ...v, interview_date: new Date(v.interview_date).toISOString(), interview_type: v.interview_type || null, meeting_link: v.meeting_link || null, notes: v.notes || null }
    return (interview ? api.put(`/interviews/${interview.id}`, body) : api.post('/interviews', body)).then((r) => r.data)
  }, { onSuccess: onClose })

  return (
    <Modal title={interview ? 'Edit interview' : 'Schedule interview'} onClose={onClose}>
      <form onSubmit={handleSubmit((v) => save.mutate(v))} className="space-y-4" noValidate>
        <Field label="Application" error={errors.application_id?.message}>
          <select {...register('application_id')} disabled={!!applicationId}>
            <option value="">Choose an application</option>
            {data?.items.map((a) => <option key={a.id} value={a.id}>{a.job_title} — {a.company_name}</option>)}
          </select>
        </Field>
        <Field label="Date and time" error={errors.interview_date?.message}><input type="datetime-local" {...register('interview_date')} /></Field>
        <Field label="Type">
          <input list="interview-types" {...register('interview_type')} placeholder="Phone screen" />
          <datalist id="interview-types">{['Phone screen', 'Technical', 'HR', 'On-site', 'Final'].map((t) => <option key={t} value={t} />)}</datalist>
        </Field>
        <Field label="Meeting link" error={errors.meeting_link?.message}><input {...register('meeting_link')} placeholder="https://" inputMode="url" /></Field>
        <Field label="Notes"><textarea {...register('notes')} /></Field>
        <ErrorNote>{save.isError ? errorMessage(save.error) : ''}</ErrorNote>
        <div className="flex justify-end gap-2">
          <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" disabled={save.isPending}>{save.isPending ? 'Saving…' : 'Save interview'}</button>
        </div>
      </form>
    </Modal>
  )
}
