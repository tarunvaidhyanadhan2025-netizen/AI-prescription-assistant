import axios, { AxiosError } from 'axios'
import type {
  UploadResponse,
  AnalysisRequest,
  FullAnalysisResponse,
  PrescriptionListResponse,
  PrescriptionSummary,
  HealthResponse,
  ApiError,
} from '@/types/api'
import type { PrescriptionAnalysis, Medicine, LifestyleRecommendation, TodayPrecaution } from '@/types/medicine'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 480_000,
  headers: { Accept: 'application/json' },
})

// ─── Error normaliser ─────────────────────────────────────────────────────────
export function parseApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosErr = error as AxiosError<ApiError>
    const data = axiosErr.response?.data
    if (data?.detail) {
      return typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)
    }
    if (data?.message) return data.message
    if (axiosErr.code === 'ECONNABORTED') return 'Request timed out. The server may be busy — please try again.'
    if (axiosErr.code === 'ERR_NETWORK') return 'Cannot reach the backend server. Make sure it is running on port 8000.'
    if (axiosErr.response?.status === 413) return 'File is too large. Please upload a smaller image.'
    if (axiosErr.response?.status === 422) return 'OCR failed. Try a clearer, well-lit photo of the prescription.'
    if (axiosErr.response?.status === 404) return 'Prescription not found. Please upload the image first.'
    if (axiosErr.response?.status === 429) return 'Too many requests. Please wait a moment before trying again.'
    if (axiosErr.response?.status && axiosErr.response.status >= 500)
      return 'Server error. The backend may be starting up — please retry in a moment.'
  }
  if (error instanceof Error) return error.message
  return 'An unexpected error occurred.'
}

// ─── Backend API calls ────────────────────────────────────────────────────────

export async function uploadPrescription(
  file: File,
  onProgress?: (pct: number) => void
): Promise<UploadResponse> {
  const form = new FormData()
  form.append('file', file)
  const { data } = await apiClient.post<UploadResponse>('/api/v1/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
  return data
}

export async function analysePresciption(request: AnalysisRequest): Promise<FullAnalysisResponse> {
  const { data } = await apiClient.post<FullAnalysisResponse>('/api/v1/analysis', request)
  return data
}

export async function getAnalysis(
  prescriptionId: string,
  patientAge?: number | null,
  language = 'en'
): Promise<FullAnalysisResponse> {
  const params: Record<string, string | number> = { language }
  if (patientAge != null) params.patient_age = patientAge
  const { data } = await apiClient.get<FullAnalysisResponse>(`/api/v1/analysis/${prescriptionId}`, { params })
  return data
}

export async function listPrescriptions(limit = 20, offset = 0): Promise<PrescriptionListResponse> {
  const { data } = await apiClient.get<PrescriptionListResponse>('/api/v1/prescriptions', {
    params: { limit, offset },
  })
  return data
}

export async function getPrescription(prescriptionId: string): Promise<PrescriptionSummary> {
  const { data } = await apiClient.get<PrescriptionSummary>(`/api/v1/prescriptions/${prescriptionId}`)
  return data
}

export async function getHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>('/api/v1/health')
  return data
}

// ─── Adapter helpers ──────────────────────────────────────────────────────────

function severityToUI(s: string): 'low' | 'moderate' | 'high' | 'critical' {
  if (s === 'medium') return 'moderate'
  if (s === 'critical') return 'critical'
  if (s === 'high') return 'high'
  return 'low'
}

function drowsinessFromBackend(
  causes: boolean,
  note: string,
  seriousSideEffects: string[]
): 'none' | 'mild' | 'moderate' | 'severe' {
  if (!causes) return 'none'
  const noteL = note.toLowerCase()
  const severe = seriousSideEffects.some((s) => s.toLowerCase().includes('drowsi') || s.toLowerCase().includes('sedati'))
  if (severe || noteL.includes('severe') || noteL.includes('do not drive')) return 'severe'
  if (noteL.includes('moderate') || noteL.includes('avoid driving')) return 'moderate'
  return 'mild'
}

/**
 * Build side effects list from backend data.
 *
 * FIX: serious_side_effects now correctly map to severity 'critical' (not 'high').
 * This ensures the card expanded view matches the severity shown in the dashboard summary.
 * The distinction:
 *   - common side_effects    → low severity  (expected, usually manageable)
 *   - serious_side_effects   → critical severity (rare but need immediate attention)
 */
function buildSideEffects(
  commonEffects: string[],
  seriousEffects: string[]
) {
  return [
    ...commonEffects.map((name, i) => ({
      id: `se-common-${i}`,
      name,
      description: name,
      severity: 'low' as const,
      frequency: 'common' as const,
    })),
    ...seriousEffects.map((name, i) => ({
      id: `se-serious-${i}`,
      name,
      description: name,
      // FIXED: was 'high', now correctly 'critical' so card matches dashboard alert
      severity: 'critical' as const,
      // Serious effects are rare; don't imply they're common
      frequency: 'rare' as const,
      actionRequired: 'Stop taking and contact your doctor immediately if this occurs.',
    })),
  ]
}

function buildAgeWarnings(warnings: string[]) {
  return warnings.map((w) => {
    const lower = w.toLowerCase()
    const ageGroup =
      lower.includes('child') || lower.includes('pediatric') || lower.includes('infant') ? 'pediatric' :
      lower.includes('elder') || lower.includes('geriatric') || lower.includes('old') ? 'geriatric' : 'adult'
    return {
      ageGroup: ageGroup as 'pediatric' | 'adult' | 'geriatric',
      warning: w,
      contraindicated: lower.includes('contraindicated') || lower.includes('not approved'),
    }
  })
}

// ─── Lifestyle recommendation builders ───────────────────────────────────────

type MedData = {
  medicine_name: string
  drug_class: string
  how_to_take: string
  contraindications: string[]
  causes_drowsiness: boolean
  drowsiness_note: string
  side_effects: string[]
  serious_side_effects: string[]
  dosage_info: string
  dosage_notes: string[]
}

function buildLifestyleRecommendations(
  m: MedData,
  idx: number,
  drowsinessLevel: string
): LifestyleRecommendation[] {
  const recs: LifestyleRecommendation[] = []
  const name = m.medicine_name
  const classL = (m.drug_class || '').toLowerCase()
  const howToL = (m.how_to_take || '').toLowerCase()
  const contraL = m.contraindications.map((c) => c.toLowerCase()).join(' ')
  const sideL = [...m.side_effects, ...m.serious_side_effects].map((s) => s.toLowerCase()).join(' ')
  let recIdx = 0
  const id = (tag: string) => `lr-${idx}-${tag}-${recIdx++}`

  // ── WHAT TO AVOID ─────────────────────────────────────────────────────────

  // Alcohol
  if (
    contraL.includes('alcohol') ||
    classL.includes('benzo') ||
    classL.includes('sedative') ||
    classL.includes('opioid') ||
    classL.includes('anxiolytic') ||
    classL.includes('antihistamine') ||
    classL.includes('muscle relax') ||
    classL.includes('antidepressant') ||
    classL.includes('antipsychotic') ||
    classL.includes('anticonvulsant') ||
    classL.includes('antibiotic') && (classL.includes('metronidazole') || contraL.includes('alcohol'))
  ) {
    const isCritical = classL.includes('benzo') || classL.includes('opioid') || classL.includes('sedative')
    recs.push({
      id: id('alcohol'),
      category: 'alcohol',
      section: 'avoid',
      title: isCritical ? 'Do NOT Consume Alcohol' : 'Avoid or Restrict Alcohol',
      description: isCritical
        ? `Combining alcohol with ${name} can cause severe CNS depression and respiratory slowing — potentially life-threatening. No alcohol during this course.`
        : `Alcohol may amplify side effects of ${name} including dizziness and sedation. Avoid alcohol throughout treatment.`,
      severity: isCritical ? 'critical' : 'high',
    })
  }

  // Grapefruit
  if (
    classL.includes('calcium channel') ||
    classL.includes('statin') ||
    classL.includes('immunosuppressant') ||
    classL.includes('cyclosporine') ||
    classL.includes('antifungal') ||
    classL.includes('benzodiazepine') ||
    name.toLowerCase().includes('amlodipine') ||
    name.toLowerCase().includes('atorvastatin') ||
    name.toLowerCase().includes('simvastatin') ||
    name.toLowerCase().includes('alprazolam')
  ) {
    recs.push({
      id: id('grapefruit'),
      category: 'diet',
      section: 'avoid',
      title: 'Avoid Grapefruit Juice',
      description: `Grapefruit and its juice block the enzyme that breaks down ${name}, causing drug levels in your blood to rise unpredictably. Avoid grapefruit and grapefruit juice throughout this course.`,
      severity: 'high',
    })
  }

  // Sunlight / photosensitivity
  if (
    classL.includes('antibiotic') ||
    classL.includes('fluoroquinolone') ||
    classL.includes('tetracycline') ||
    classL.includes('sulfonamide') ||
    classL.includes('diuretic') ||
    classL.includes('nsaid') ||
    classL.includes('retinoid') ||
    sideL.includes('photosensitiv') ||
    contraL.includes('sun')
  ) {
    recs.push({
      id: id('sunlight'),
      category: 'sunlight',
      section: 'avoid',
      title: 'Limit Direct Sunlight',
      description: `${name} may increase your skin's sensitivity to UV radiation. Avoid prolonged sun exposure, apply SPF 30+ sunscreen, and wear protective clothing when outdoors during treatment.`,
      severity: 'moderate',
    })
  }

  // Driving / heavy machinery
  if (m.causes_drowsiness || drowsinessLevel !== 'none') {
    const isSevere = drowsinessLevel === 'severe'
    recs.push({
      id: id('driving'),
      category: 'driving',
      section: 'avoid',
      title: isSevere ? 'Do NOT Drive or Operate Machinery' : 'Use Caution When Driving',
      description: isSevere
        ? `${name} causes significant sedation. Do not drive, cycle, or operate heavy machinery at all during this course.`
        : (m.drowsiness_note || `${name} may cause drowsiness or impair concentration. Assess how you feel before driving. Avoid driving if affected.`),
      severity: isSevere ? 'critical' : 'moderate',
    })
  }

  // Supplements / mineral interactions
  if (
    classL.includes('antibiotic') ||
    classL.includes('fluoroquinolone') ||
    classL.includes('tetracycline') ||
    classL.includes('bisphosphonate') ||
    classL.includes('thyroid') ||
    name.toLowerCase().includes('levothyroxine') ||
    name.toLowerCase().includes('ciprofloxacin') ||
    name.toLowerCase().includes('doxycycline')
  ) {
    recs.push({
      id: id('supplements'),
      category: 'supplement',
      section: 'avoid',
      title: 'Space Out Calcium, Iron & Antacids',
      description: `Do not take calcium supplements, iron tablets, or antacids within 2 hours of ${name}. These minerals bind to the drug in the gut and can significantly reduce its absorption and effectiveness.`,
      severity: 'high',
    })
  }

  // Herbal interactions
  if (
    classL.includes('anticoagulant') ||
    classL.includes('antidepressant') ||
    classL.includes('immunosuppressant') ||
    classL.includes('anticonvulsant') ||
    classL.includes('ssri') ||
    classL.includes('snri') ||
    classL.includes('maoi')
  ) {
    recs.push({
      id: id('herbal'),
      category: 'supplement',
      section: 'avoid',
      title: 'Avoid Herbal Supplements Without Checking',
      description: `Supplements such as St John's Wort, ginkgo, ginseng, or valerian may interact with ${name}. Always inform your pharmacist of any herbal or OTC products you are taking.`,
      severity: 'moderate',
    })
  }

  // NSAIDs / OTC pain relief warning for anticoagulants or steroids
  if (
    classL.includes('anticoagulant') ||
    classL.includes('antiplatelet') ||
    classL.includes('corticosteroid') ||
    classL.includes('steroid')
  ) {
    recs.push({
      id: id('nsaid'),
      category: 'other',
      section: 'avoid',
      title: 'Avoid OTC NSAIDs (Ibuprofen, Aspirin)',
      description: `Over-the-counter pain relievers containing ibuprofen, aspirin, or naproxen can increase bleeding risk or stomach ulcers when combined with ${name}. Use paracetamol instead, or ask your pharmacist.`,
      severity: 'high',
    })
  }

  // Strenuous exercise — antihypertensives, diuretics, beta-blockers
  if (
    classL.includes('antihypertensive') ||
    classL.includes('diuretic') ||
    classL.includes('beta-blocker') ||
    classL.includes('ace inhibitor') ||
    classL.includes('calcium channel') ||
    classL.includes('vasodilator') ||
    classL.includes('hypoglycaemic') ||
    classL.includes('antidiabetic')
  ) {
    recs.push({
      id: id('exercise-caution'),
      category: 'activity',
      section: 'avoid',
      title: 'Avoid Sudden Strenuous Exercise',
      description: `${name} can cause dizziness or a sudden drop in blood pressure, especially during or just after vigorous activity. Warm up gradually, stay hydrated, and stop if you feel faint or light-headed.`,
      severity: 'moderate',
    })
  }

  // ── BEST PRACTICES ────────────────────────────────────────────────────────

  // With food or without food
  if (howToL.includes('food') || howToL.includes('meal') || m.dosage_info.toLowerCase().includes('food')) {
    const withFood = howToL.includes('with') || m.dosage_info.toLowerCase().includes('with food')
    recs.push({
      id: id('food-intake'),
      category: 'diet',
      section: 'bestPractice',
      title: withFood ? `Take ${name} With Food` : `Take ${name} on an Empty Stomach`,
      description: withFood
        ? `Taking ${name} with a meal reduces stomach irritation and improves tolerability. A light meal is sufficient — you do not need a full meal.`
        : `Take ${name} at least 30 minutes before meals or 2 hours after eating for best absorption. Food in the stomach reduces how much reaches your bloodstream.`,
      severity: 'moderate',
    })
  } else {
    // Default: always with water
    recs.push({
      id: id('water'),
      category: 'other',
      section: 'bestPractice',
      title: 'Take With a Full Glass of Water',
      description: `Swallow ${name} with at least 200 ml (a full glass) of water to aid swallowing, reduce throat irritation, and ensure proper dissolution in the stomach.`,
      severity: 'low',
    })
  }

  // Do not crush (extended release, enteric coated)
  if (
    m.dosage_info.toLowerCase().includes('sr') ||
    m.dosage_info.toLowerCase().includes('xr') ||
    m.dosage_info.toLowerCase().includes('er') ||
    m.dosage_info.toLowerCase().includes('extended') ||
    m.dosage_info.toLowerCase().includes('enteric') ||
    m.dosage_notes.some((n) => n.toLowerCase().includes('crush') || n.toLowerCase().includes('chew'))
  ) {
    recs.push({
      id: id('no-crush'),
      category: 'other',
      section: 'bestPractice',
      title: 'Do Not Crush or Split Tablet',
      description: `${name} is designed with a special coating that controls how the drug is released. Crushing or splitting destroys this mechanism and may cause too much drug to enter your system at once.`,
      severity: 'high',
    })
  }

  // Same time every day
  recs.push({
    id: id('timing'),
    category: 'sleep',
    section: 'bestPractice',
    title: 'Take at the Same Time Every Day',
    description: `Consistency in timing helps maintain a steady level of ${name} in your bloodstream and improves treatment outcomes. Set a daily reminder if needed.`,
    severity: 'low',
  })

  // Complete the course (antibiotics)
  if (classL.includes('antibiotic') || classL.includes('antifungal') || classL.includes('antiviral')) {
    recs.push({
      id: id('full-course'),
      category: 'other',
      section: 'bestPractice',
      title: 'Complete the Full Course',
      description: `Do not stop ${name} early even if you feel better. Incomplete courses allow resistant organisms to survive and the infection to return. Take every dose as prescribed.`,
      severity: 'high',
    })
  }

  // Storage note for insulin / refrigerated meds
  if (
    classL.includes('insulin') ||
    name.toLowerCase().includes('insulin') ||
    m.dosage_info.toLowerCase().includes('inject') ||
    m.how_to_take.toLowerCase().includes('inject')
  ) {
    recs.push({
      id: id('storage-cool'),
      category: 'other',
      section: 'bestPractice',
      title: 'Store Correctly — Refrigerate If Unused',
      description: `Unopened ${name} should be stored in the refrigerator (2–8°C). Once in use, it can typically be kept at room temperature for up to 28 days. Discard if it looks cloudy or discoloured.`,
      severity: 'moderate',
    })
  }

  // ── SUPPORTIVE LIFESTYLE ──────────────────────────────────────────────────

  // Hydration — always useful, especially antibiotics, diuretics
  recs.push({
    id: id('hydration'),
    category: 'activity',
    section: 'supportive',
    title: 'Maintain Good Hydration',
    description: 'Drink 6–8 glasses of water daily throughout your treatment. Adequate hydration supports kidney function, helps distribute the medication, and reduces the risk of side effects like constipation or kidney strain.',
    severity: 'low',
  })

  // Sleep
  if (
    classL.includes('benzo') ||
    classL.includes('sedative') ||
    classL.includes('antidepressant') ||
    classL.includes('antipsychotic') ||
    classL.includes('anxiolytic') ||
    classL.includes('antihypertensive') ||
    m.causes_drowsiness
  ) {
    recs.push({
      id: id('sleep'),
      category: 'sleep',
      section: 'supportive',
      title: 'Follow a Regular Sleep Schedule',
      description: `Consistent sleep supports the effects of ${name} and aids recovery. Aim for 7–8 hours at the same time each night. Avoid screens for 30 minutes before bed.`,
      severity: 'low',
    })
  }

  // Diet quality
  if (
    classL.includes('antidiabetic') ||
    classL.includes('antihypertensive') ||
    classL.includes('lipid') ||
    classL.includes('statin') ||
    classL.includes('biguanide') ||
    classL.includes('antiobesity')
  ) {
    recs.push({
      id: id('diet-quality'),
      category: 'diet',
      section: 'supportive',
      title: 'Reduce Processed Foods & Sugar',
      description: `A balanced diet with less refined carbohydrates, sodium, and saturated fat works alongside ${name} to improve treatment outcomes. Prioritise vegetables, whole grains, lean proteins, and legumes.`,
      severity: 'low',
    })
  }

  // Stress management
  recs.push({
    id: id('stress'),
    category: 'activity',
    section: 'supportive',
    title: 'Manage Stress Where Possible',
    description: 'Chronic stress can worsen many conditions this medication is treating. Simple techniques such as deep breathing, short walks, or relaxation exercises can complement your treatment.',
    severity: 'low',
  })

  return recs
}

function buildTodaysPrecautions(
  m: MedData,
  idx: number,
  drowsinessLevel: string
): TodayPrecaution[] {
  const precautions: TodayPrecaution[] = []
  const classL = (m.drug_class || '').toLowerCase()
  const contraL = m.contraindications.map((c) => c.toLowerCase()).join(' ')
  let pIdx = 0
  const id = () => `tp-${idx}-${pIdx++}`

  // Alcohol — highest priority
  if (
    contraL.includes('alcohol') ||
    classL.includes('benzo') ||
    classL.includes('opioid') ||
    classL.includes('sedative') ||
    classL.includes('antibiotic')
  ) {
    precautions.push({
      id: id(),
      emoji: '🚫',
      text: 'Avoid alcohol today and throughout this course.',
      severity: classL.includes('benzo') || classL.includes('opioid') ? 'critical' : 'high',
    })
  }

  // Driving
  if (m.causes_drowsiness || drowsinessLevel !== 'none') {
    const isSevere = drowsinessLevel === 'severe'
    precautions.push({
      id: id(),
      emoji: '🚗',
      text: isSevere
        ? `Do not drive or operate machinery — ${m.medicine_name} causes significant drowsiness.`
        : 'This medicine may cause drowsiness; do not drive if you feel affected.',
      severity: isSevere ? 'critical' : 'moderate',
    })
  }

  // Sunlight
  if (
    classL.includes('antibiotic') ||
    classL.includes('fluoroquinolone') ||
    classL.includes('tetracycline') ||
    classL.includes('diuretic') ||
    classL.includes('nsaid')
  ) {
    precautions.push({
      id: id(),
      emoji: '☀️',
      text: 'Avoid prolonged direct sunlight; use SPF 30+ sunscreen if going outdoors.',
      severity: 'moderate',
    })
  }

  // Take dose today
  precautions.push({
    id: id(),
    emoji: '💊',
    text: `Do not skip today's dose of ${m.medicine_name}; take it at your usual time.`,
    severity: 'moderate',
  })

  // Hydration
  precautions.push({
    id: id(),
    emoji: '💧',
    text: 'Drink plenty of water today — at least 6–8 glasses.',
    severity: 'low',
  })

  // Serious side effect warning
  if (m.serious_side_effects.length > 0) {
    const firstEffect = m.serious_side_effects[0]
    precautions.push({
      id: id(),
      emoji: '⚠️',
      text: `Seek medical attention immediately if you experience: ${firstEffect.toLowerCase()}.`,
      severity: 'critical',
    })
  } else if (contraL.includes('rash') || contraL.includes('breathing')) {
    precautions.push({
      id: id(),
      emoji: '⚠️',
      text: 'Seek medical attention if severe rash, swelling, or difficulty breathing occurs.',
      severity: 'critical',
    })
  }

  // Grapefruit
  if (
    classL.includes('calcium channel') ||
    classL.includes('statin') ||
    classL.includes('benzodiazepine') ||
    m.medicine_name.toLowerCase().includes('amlodipine') ||
    m.medicine_name.toLowerCase().includes('alprazolam')
  ) {
    precautions.push({
      id: id(),
      emoji: '🍊',
      text: 'Avoid grapefruit juice — it can raise drug levels in your blood unpredictably.',
      severity: 'high',
    })
  }

  // Limit to 6 max, prioritise by severity
  const RANK: Record<string, number> = { critical: 0, high: 1, moderate: 2, low: 3 }
  return precautions
    .sort((a, b) => (RANK[a.severity] ?? 4) - (RANK[b.severity] ?? 4))
    .slice(0, 6)
}

// ─── Main adapter ─────────────────────────────────────────────────────────────

export function adaptBackendToUI(full: FullAnalysisResponse): PrescriptionAnalysis {
  const medicines: Medicine[] = full.medicines.map((m, idx) => {
    const sideEffects = buildSideEffects(m.side_effects, m.serious_side_effects)
    const drowsinessLevel = drowsinessFromBackend(m.causes_drowsiness, m.drowsiness_note, m.serious_side_effects)

    const dosage = {
      standard: m.dosage_info || 'As directed by your doctor',
      maximum: m.dosage_notes.find((n) => n.toLowerCase().includes('max')) || 'As prescribed',
      frequency: m.how_to_take || m.dosage_info || 'As directed',
      route: 'Oral',
      withFood: m.how_to_take.toLowerCase().includes('food') || m.how_to_take.toLowerCase().includes('meal'),
      withWater: true,
      missedDose: m.dosage_notes.find((n) => n.toLowerCase().includes('miss')) ||
        'Take as soon as you remember. Skip if next dose is near. Never double up.',
      overdoseWarning: m.serious_side_effects.length > 0
        ? 'If you suspect overdose, seek emergency medical attention immediately.'
        : undefined,
    }

    const isAlcohol = m.contraindications.some((c) => c.toLowerCase().includes('alcohol'))
    const interactions = isAlcohol ? [{
      id: `int-alcohol-${idx}`,
      drugName: 'Alcohol',
      severity: 'high' as const,
      description: 'Alcohol may interact with this medication.',
      recommendation: 'Avoid alcohol while taking this medicine.',
    }] : []

    const lifestyleRecs = buildLifestyleRecommendations(m, idx, drowsinessLevel)
    const todaysPrecautions = buildTodaysPrecautions(m, idx, drowsinessLevel)

    return {
      id: `med-${idx}-${m.medicine_name.replace(/\s+/g, '-').toLowerCase()}`,
      name: m.medicine_name,
      genericName: m.drug_class ? `${m.medicine_name} (${m.drug_class})` : m.medicine_name,
      brandNames: [],
      drugClass: m.drug_class || 'Prescription Medicine',
      indication: m.use_case || 'As prescribed',
      description: m.explanation || 'This medicine is prescribed by your doctor.',
      mechanism: m.mechanism || '',
      dosage,
      sideEffects,
      interactions,
      drowsinessLevel,
      ageWarnings: buildAgeWarnings(m.age_warnings),
      lifestyleRecommendations: lifestyleRecs,
      todaysPrecautions,
      requiresPrescription: true,
      storageInstructions: 'Store at room temperature. Keep away from children.',
      severity_level: m.severity_level,
      generated_by: m.generated_by,
      contraindications: m.contraindications,
      dosage_notes: m.dosage_notes,
    }
  })

  const overallWarnings: string[] = []
  if (full.overall_drowsiness_warning) overallWarnings.push('One or more medicines may cause drowsiness. Avoid driving or operating machinery.')
  if (full.overall_dosage_concern) overallWarnings.push('Dosage concerns detected. Review with your pharmacist.')
  if (full.overall_age_warning) overallWarnings.push('Age-specific warnings noted. Consult your doctor if in doubt.')

  // ── Awareness Alerts — HIGH threshold ────────────────────────────────────
  // Only surface genuinely important clinical warnings. Minor or common side
  // effects are deliberately excluded even if labelled 'critical' internally.
  //
  // An alert is generated ONLY when ALL of the following are true:
  //   (a) the medicine's overall severity_level is 'critical'  AND
  //   (b) at least one of:
  //       - there is a real serious_side_effect string from the backend, OR
  //       - the medicine is contraindicated (contraindications array non-empty), OR
  //       - drowsiness is severe (patient-safety risk while driving/machinery)
  //
  // Medicines that merely have common side effects mapped to 'critical' severity
  // internally (e.g. sunscreen with contact-dermatitis risk, moisturisers, OTC
  // supplements) are filtered out by requiring severity_level === 'critical'
  // from the backend — the authoritative source for clinical significance.
  const criticalAlerts: string[] = medicines
    .filter((m) => {
      const raw = full.medicines.find((r) => r.medicine_name === m.name)
      const hasBackendSeriousEffect = (raw?.serious_side_effects ?? []).some(
        (s) => s.trim().toLowerCase() !== 'none' && s.trim() !== ''
      )
      const hasContraindication = (raw?.contraindications ?? []).some(
        (c) => c.trim().toLowerCase() !== 'none' && c.trim() !== ''
      )
      const isSevereDrowsiness = m.drowsinessLevel === 'severe'

      // Gate 1: backend must classify as critical (not just a frontend mapping)
      const backendCritical = m.severity_level === 'critical'

      // Gate 2: must have at least one real clinical reason
      const hasRealReason = hasBackendSeriousEffect || hasContraindication || isSevereDrowsiness

      return backendCritical && hasRealReason
    })
    .map((m) => {
      const raw = full.medicines.find((r) => r.medicine_name === m.name)
      // Pick the most clinically meaningful reason to surface
      const seriousEffect = (raw?.serious_side_effects ?? []).find(
        (s) => s.trim().toLowerCase() !== 'none' && s.trim() !== ''
      )
      const contraindication = (raw?.contraindications ?? []).find(
        (c) => c.trim().toLowerCase() !== 'none' && c.trim() !== ''
      )
      const reason =
        seriousEffect ||
        (m.drowsinessLevel === 'severe' ? 'Severe drowsiness — do not drive or operate machinery' : null) ||
        contraindication ||
        'Critical safety profile — consult your doctor or pharmacist'
      return `${m.name}: ${reason}`
    })

  // Merge all todaysPrecautions across medicines, deduplicate by emoji+text,
  // keep top 6 most severe
  const RANK: Record<string, number> = { critical: 0, high: 1, moderate: 2, low: 3 }
  const seen = new Set<string>()
  const allPrecautions = medicines
    .flatMap((med) => med.todaysPrecautions ?? [])
    .filter((p) => {
      const key = `${p.emoji}${p.text.slice(0, 30)}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
    .sort((a, b) => (RANK[a.severity] ?? 4) - (RANK[b.severity] ?? 4))
    .slice(0, 6)

  return {
    id: full.prescription_id,
    prescription_id: full.prescription_id,
    patientAge: full.patient_age ?? undefined,
    rawText: full.medicines.map((m) => m.medicine_name).join(', '),
    extractedMedicines: medicines,
    overallWarnings,
    criticalAlerts,
    allPrecautions,
    analysisTimestamp: new Date().toISOString(),
    confidence: 0.85,
    provider_used: full.provider_used,
    overall_severity: full.overall_severity,
    overall_drowsiness_warning: full.overall_drowsiness_warning,
    overall_dosage_concern: full.overall_dosage_concern,
  }
}

export async function mockAnalyzePrescription(
  _request: Record<string, unknown>
): Promise<{ success: boolean; data?: PrescriptionAnalysis; error?: string }> {
  await new Promise((r) => setTimeout(r, 2600))
  const { MOCK_ANALYSIS } = await import('./mockData')
  return { success: true, data: MOCK_ANALYSIS }
}

export default apiClient
