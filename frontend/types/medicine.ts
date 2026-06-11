// ─── UI-layer medicine types (used by new frontend components) ───────────────
export type SeverityLevel = 'low' | 'moderate' | 'high' | 'critical'
export type DrowsinessLevel = 'none' | 'mild' | 'moderate' | 'severe'
export type AgeGroup = 'pediatric' | 'adult' | 'geriatric' | 'all'

export interface SideEffect {
  id: string
  name: string
  description: string
  severity: SeverityLevel
  frequency: 'common' | 'uncommon' | 'rare'
  actionRequired?: string
}

export interface DrugInteraction {
  id: string
  drugName: string
  severity: SeverityLevel
  description: string
  recommendation: string
}

export interface DosageInfo {
  standard: string
  maximum: string
  frequency: string
  route: string
  withFood: boolean
  withWater: boolean
  missedDose?: string
  overdoseWarning?: string
}

export interface AgeWarning {
  ageGroup: AgeGroup
  warning: string
  contraindicated: boolean
  adjustedDose?: string
}

export interface LifestyleRecommendation {
  id: string
  category: 'diet' | 'activity' | 'alcohol' | 'sunlight' | 'sleep' | 'driving' | 'other' | 'supplement' | 'smoking' | 'caffeine'
  /** Which of the three lifestyle sections this belongs to */
  section: 'avoid' | 'bestPractice' | 'supportive'
  title: string
  description: string
  severity: SeverityLevel
}

export interface TodayPrecaution {
  id: string
  emoji: string
  text: string
  severity: SeverityLevel
}

export interface Medicine {
  id: string
  name: string
  genericName: string
  brandNames: string[]
  drugClass: string
  indication: string
  description: string
  mechanism: string
  dosage: DosageInfo
  sideEffects: SideEffect[]
  interactions: DrugInteraction[]
  drowsinessLevel: DrowsinessLevel
  ageWarnings: AgeWarning[]
  lifestyleRecommendations: LifestyleRecommendation[]
  todaysPrecautions: TodayPrecaution[]
  pregnancyCategory?: string
  controlledSubstance?: boolean
  requiresPrescription: boolean
  storageInstructions: string
  // Backend-passthrough fields (kept for display in expanded mode)
  severity_level?: string
  generated_by?: string
  contraindications?: string[]
  dosage_notes?: string[]
}

export interface PrescriptionAnalysis {
  id: string
  patientAge?: number
  rawText: string
  extractedMedicines: Medicine[]
  overallWarnings: string[]
  criticalAlerts: string[]
  analysisTimestamp: string
  confidence: number
  // Backend passthrough
  prescription_id?: string
  provider_used?: string
  overall_severity?: string
  overall_drowsiness_warning?: boolean
  overall_dosage_concern?: boolean
  /** Merged, deduplicated top precautions across all medicines */
  allPrecautions?: TodayPrecaution[]
}
