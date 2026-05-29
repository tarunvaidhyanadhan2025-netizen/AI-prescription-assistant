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
  category: 'diet' | 'activity' | 'alcohol' | 'sunlight' | 'sleep' | 'driving' | 'other'
  title: string
  description: string
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
  pregnancyCategory?: string
  controlledSubstance?: boolean
  requiresPrescription: boolean
  storageInstructions: string
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
}
