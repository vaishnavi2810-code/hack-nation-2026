import { useEffect, useState } from 'react'
import { Eye, PencilLine, Plus, Search, Trash2, UsersRound } from 'lucide-react'
import StatusBadge from '../components/StatusBadge'
import { apiRequest, API_PATHS, HTTP } from '../lib/api'

type PatientRecord = {
  id: string
  name: string
  phone: string
  email?: string | null
  notes?: string | null
  created_at?: string | null
  last_appointment?: string | null
}

const FALLBACK_PATIENTS = [
  {
    id: 'pat-001',
    name: 'Hannah Lee',
    lastVisit: 'Jan 28, 2026',
    nextStep: 'Annual physical follow-up',
    status: 'Active care plan',
  },
  {
    id: 'pat-002',
    name: 'Jordan Patel',
    lastVisit: 'Jan 30, 2026',
    nextStep: 'Lab results review',
    status: 'Awaiting confirmation',
  },
  {
    id: 'pat-003',
    name: 'Maya Rivera',
    lastVisit: 'Feb 2, 2026',
    nextStep: 'Telehealth check-in',
    status: 'Confirmed visit',
  },
  {
    id: 'pat-004',
    name: 'Carlos Diaz',
    lastVisit: 'Feb 4, 2026',
    nextStep: 'Reschedule requested',
    status: 'Needs follow-up',
  },
]

const STATUS_LOADING = 'Loading patients...'
const STATUS_LOAD_ERROR = 'Unable to load patients.'
const STATUS_ACTION_ERROR = 'Unable to complete patient action.'

const PROMPT_PATIENT_NAME = 'Enter patient name'
const PROMPT_PATIENT_PHONE = 'Enter patient phone'
const PROMPT_PATIENT_EMAIL = 'Enter patient email (optional)'
const PROMPT_PATIENT_NOTES = 'Enter patient notes (optional)'

const EMPTY_VALUE = '—'
const DEFAULT_PATIENT_STATUS = 'Active care plan'
const VIEW_PATIENT_SEPARATOR = ' · '

const PatientsPage = () => {
  const [patients, setPatients] = useState(FALLBACK_PATIENTS)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)

  const loadPatients = async () => {
    setStatusMessage(STATUS_LOADING)
    const result = await apiRequest<PatientRecord[]>(API_PATHS.PATIENTS, {
      method: HTTP.GET,
      requiresAuth: true,
    })

    if (result.error) {
      setStatusMessage(STATUS_LOAD_ERROR)
      return
    }

    if (result.data && result.data.length > 0) {
      const mappedPatients = result.data.map((patient) => ({
        id: patient.id,
        name: patient.name,
        lastVisit: patient.last_appointment ?? EMPTY_VALUE,
        nextStep: patient.notes ?? EMPTY_VALUE,
        status: DEFAULT_PATIENT_STATUS,
      }))
      setPatients(mappedPatients)
    }
    setStatusMessage(null)
  }

  useEffect(() => {
    loadPatients()
  }, [])

  const handleCreatePatient = async () => {
    const name = window.prompt(PROMPT_PATIENT_NAME)
    if (!name) {
      return
    }
    const phone = window.prompt(PROMPT_PATIENT_PHONE)
    if (!phone) {
      return
    }
    const email = window.prompt(PROMPT_PATIENT_EMAIL) ?? undefined
    const notes = window.prompt(PROMPT_PATIENT_NOTES) ?? undefined

    const result = await apiRequest(API_PATHS.PATIENTS, {
      method: HTTP.POST,
      requiresAuth: true,
      body: {
        name,
        phone,
        email,
        notes,
      },
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadPatients()
  }

  const handleViewPatient = async (patientId: string) => {
    const result = await apiRequest<PatientRecord>(API_PATHS.PATIENT_BY_ID(patientId), {
      method: HTTP.GET,
      requiresAuth: true,
    })

    if (result.error || !result.data) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    window.alert(`${result.data.name}${VIEW_PATIENT_SEPARATOR}${result.data.phone}`)
  }

  const handleUpdatePatient = async (patientId: string) => {
    const name = window.prompt(PROMPT_PATIENT_NAME)
    const phone = window.prompt(PROMPT_PATIENT_PHONE)
    const email = window.prompt(PROMPT_PATIENT_EMAIL)
    const notes = window.prompt(PROMPT_PATIENT_NOTES)

    const result = await apiRequest(API_PATHS.PATIENT_BY_ID(patientId), {
      method: HTTP.PUT,
      requiresAuth: true,
      body: {
        name: name || undefined,
        phone: phone || undefined,
        email: email || undefined,
        notes: notes || undefined,
      },
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadPatients()
  }

  const handleDeletePatient = async (patientId: string) => {
    const result = await apiRequest(API_PATHS.PATIENT_BY_ID(patientId), {
      method: HTTP.DELETE,
      requiresAuth: true,
    })

    if (result.error) {
      setStatusMessage(STATUS_ACTION_ERROR)
      return
    }

    loadPatients()
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">My patients</h1>
        <p className="mt-1 text-sm text-slate-600">
          Manage patient records tied to appointments and call activity.
        </p>
        </div>
        <button
          type="button"
          onClick={handleCreatePatient}
          className="inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
        >
          <Plus className="h-4 w-4" />
          Add patient
        </button>
      </div>

      {statusMessage && <StatusBadge label={statusMessage} variant="info" />}

      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-soft">
        <Search className="h-4 w-4 text-slate-400" />
        <input
          type="search"
          placeholder="Search patients by name or last visit"
          className="flex-1 text-sm text-slate-700 outline-none"
        />
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <UsersRound className="h-4 w-4" />
          {patients.length} active patients
        </div>
      </div>

      <div className="overflow-x-auto rounded-3xl border border-slate-200 bg-white shadow-soft">
        <table className="min-w-[720px] w-full table-fixed text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-6 py-4 w-[24%]">Patient</th>
              <th className="px-6 py-4 w-[18%]">Last visit</th>
              <th className="px-6 py-4 w-[26%]">Next step</th>
              <th className="px-6 py-4 w-[14%]">Status</th>
              <th className="px-6 py-4 w-[18%]">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {patients.map((patient) => {
              const variant =
                patient.status === 'Needs follow-up' || patient.status === 'Awaiting confirmation'
                  ? 'warning'
                  : 'success'

              return (
                <tr key={patient.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4 font-semibold text-slate-900">{patient.name}</td>
                  <td className="px-6 py-4 text-slate-600">{patient.lastVisit}</td>
                  <td className="px-6 py-4 text-slate-600">{patient.nextStep}</td>
                  <td className="px-6 py-4">
                    <StatusBadge label={patient.status} variant={variant} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3 text-xs font-semibold text-slate-600">
                      <button
                        type="button"
                        onClick={() => handleViewPatient(patient.id)}
                        className="inline-flex items-center gap-1 text-primary"
                      >
                        <Eye className="h-3.5 w-3.5" />
                        View
                      </button>
                      <button
                        type="button"
                        onClick={() => handleUpdatePatient(patient.id)}
                        className="inline-flex items-center gap-1 text-slate-500"
                      >
                        <PencilLine className="h-3.5 w-3.5" />
                        Edit
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeletePatient(patient.id)}
                        className="inline-flex items-center gap-1 text-rose-500"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default PatientsPage
