import type { PrescriptionAnalysis } from '@/types/medicine'

export const MOCK_ANALYSIS: PrescriptionAnalysis = {
  id: 'mock-001',
  patientAge: 45,
  rawText: `Dr. Arjun Mehta  MBBS, MD
City General Hospital, Mumbai — Reg. No. MH-12345

Patient: Ramesh Kumar   Age: 45 M   Date: 01-Nov-2024

Rx:
1. Tab Metformin 500mg  — BD × 30 days  (with meals)
2. Tab Amlodipine 5mg   — OD × 30 days  (morning)
3. Tab Alprazolam 0.25mg — HS × 10 days (bedtime)

Advice: Low-salt diet. Monitor BP daily. Follow up in 4 weeks.
                                    Dr. Arjun Mehta`,
  confidence: 0.91,
  analysisTimestamp: new Date().toISOString(),
  overallWarnings: [
    'Alprazolam (benzodiazepine) may interact with other CNS depressants including antihistamines and alcohol.',
    'Monitor blood pressure regularly while on Amlodipine, especially when changing posture.',
  ],
  allPrecautions: [
    { id: 'all-1', emoji: '🚫', text: 'Absolutely no alcohol — especially critical with Alprazolam (potentially fatal).', severity: 'critical' as const },
    { id: 'all-2', emoji: '🚗', text: 'Do NOT drive today — Alprazolam causes significant drowsiness and impairs reaction time.', severity: 'critical' as const },
    { id: 'all-3', emoji: '⚠️', text: 'Do not stop Alprazolam abruptly — always taper under medical supervision.', severity: 'critical' as const },
    { id: 'all-4', emoji: '🍊', text: 'Avoid grapefruit juice — it interacts with both Amlodipine and Alprazolam.', severity: 'high' as const },
    { id: 'all-5', emoji: '💊', text: "Take all three medicines at their prescribed times today — do not skip any dose.", severity: 'moderate' as const },
    { id: 'all-6', emoji: '💧', text: 'Drink at least 6–8 glasses of water today to support your treatment.', severity: 'low' as const },
  ],
  criticalAlerts: [
    'Alprazolam is Schedule H1 controlled substance — follow prescribed dose strictly. Do not stop abruptly.',
  ],
  extractedMedicines: [
    {
      id: 'med-001',
      name: 'Metformin',
      genericName: 'Metformin Hydrochloride',
      brandNames: ['Glycomet', 'Glucophage', 'Obimet', 'Walaphage'],
      drugClass: 'Biguanide / Antidiabetic',
      indication: 'Type 2 Diabetes Mellitus',
      description:
        'Metformin is the first-line oral antidiabetic medication for managing blood glucose in type 2 diabetes. It reduces hepatic glucose output and improves peripheral insulin sensitivity without causing hypoglycaemia.',
      mechanism:
        'Activates AMP-activated protein kinase (AMPK), suppresses hepatic gluconeogenesis, and improves glucose uptake in peripheral tissues via GLUT4 translocation.',
      dosage: {
        standard: '500 mg twice daily (BD)',
        maximum: '2500 mg/day',
        frequency: 'Twice daily with meals',
        route: 'Oral',
        withFood: true,
        withWater: true,
        missedDose:
          'Take as soon as remembered unless the next dose is within 2 hours. Never double the dose.',
        overdoseWarning:
          'Lactic acidosis risk — nausea, abdominal pain, weakness, breathing difficulty. Seek emergency care immediately.',
      },
      sideEffects: [
        {
          id: 'se-001',
          name: 'Nausea & Vomiting',
          description: 'Mild gastric discomfort, particularly at initiation or dose escalation.',
          severity: 'low',
          frequency: 'common',
        },
        {
          id: 'se-002',
          name: 'Diarrhoea',
          description: 'Loose stools especially in the first few weeks; usually resolves with continued use.',
          severity: 'low',
          frequency: 'common',
        },
        {
          id: 'se-003',
          name: 'Vitamin B12 Deficiency',
          description: 'Long-term use reduces intestinal B12 absorption via calcium-dependent mechanism.',
          severity: 'moderate',
          frequency: 'uncommon',
          actionRequired: 'Monitor serum B12 annually; supplement if levels fall below normal range.',
        },
        {
          id: 'se-004',
          name: 'Lactic Acidosis',
          description:
            'Rare but potentially fatal buildup of lactic acid, especially in renal impairment.',
          severity: 'critical',
          frequency: 'rare',
          actionRequired:
            'Stop medication immediately and seek emergency care if you experience unusual muscle pain, difficulty breathing, or dizziness.',
        },
      ],
      interactions: [
        {
          id: 'int-001',
          drugName: 'Iodinated Contrast Dye',
          severity: 'high',
          description:
            'Risk of contrast-induced nephropathy leading to metformin accumulation and lactic acidosis.',
          recommendation:
            'Withhold metformin 48 hours before any contrast imaging procedure. Resume only after kidney function is confirmed normal.',
        },
        {
          id: 'int-002',
          drugName: 'Alcohol',
          severity: 'moderate',
          description: 'Potentiates lactic acid production and masks hypoglycaemia symptoms.',
          recommendation: 'Limit alcohol consumption strictly. Avoid binge drinking entirely.',
        },
      ],
      drowsinessLevel: 'none',
      ageWarnings: [
        {
          ageGroup: 'geriatric',
          warning:
            'Use with caution in patients >70 years; renal function monitoring (eGFR) is essential before prescribing.',
          contraindicated: false,
          adjustedDose: 'Start at 500 mg OD; titrate slowly. Contraindicated if eGFR < 30 mL/min.',
        },
        {
          ageGroup: 'pediatric',
          warning: 'Not approved for children under 10 years of age.',
          contraindicated: true,
        },
      ],
      lifestyleRecommendations: [
        {
          id: 'lr-001',
          category: 'diet',
          section: 'avoid' as const,
          title: 'Low Glycaemic Diet',
          description:
            'Avoid refined carbohydrates, sugary drinks, and white rice. Prefer whole grains, lentils, and vegetables.',
          severity: 'moderate',
        },
        {
          id: 'lr-002',
          category: 'activity',
          section: 'supportive' as const,
          title: 'Regular Aerobic Exercise',
          description:
            'At least 150 minutes of moderate exercise per week significantly improves insulin sensitivity.',
          severity: 'low',
        },
        {
          id: 'lr-003',
          category: 'alcohol',
          section: 'avoid' as const,
          title: 'Restrict Alcohol',
          description:
            'Alcohol increases lactic acidosis risk and impairs blood glucose control.',
          severity: 'high',
        },
      ],
      todaysPrecautions: [
        { id: 'tp-met-1', emoji: '🚫', text: 'Limit alcohol intake — it increases lactic acid risk and impairs blood sugar control.', severity: 'high' as const },
        { id: 'tp-met-2', emoji: '💊', text: "Do not skip today's dose of Metformin; take it at your usual meal time.", severity: 'moderate' as const },
        { id: 'tp-met-3', emoji: '💧', text: 'Drink plenty of water today — at least 6–8 glasses.', severity: 'low' as const },
        { id: 'tp-met-4', emoji: '⚠️', text: 'Seek medical attention if you feel unusual muscle pain, difficulty breathing, or sudden weakness.', severity: 'critical' as const },
        { id: 'tp-met-5', emoji: '🍽️', text: 'Take Metformin with food to reduce stomach discomfort.', severity: 'moderate' as const },
      ],
      requiresPrescription: true,
      storageInstructions: 'Store at 15–30°C; protect from moisture and direct sunlight.',
    },
    {
      id: 'med-002',
      name: 'Amlodipine',
      genericName: 'Amlodipine Besylate',
      brandNames: ['Norvasc', 'Amlong', 'Stamlo', 'Amlip'],
      drugClass: 'Dihydropyridine Calcium Channel Blocker',
      indication: 'Hypertension, Stable Angina',
      description:
        'Amlodipine is a long-acting calcium channel blocker that relaxes arterial smooth muscle, reducing peripheral vascular resistance and blood pressure. It is well-tolerated and requires once-daily dosing.',
      mechanism:
        'Selectively inhibits calcium ion influx across smooth muscle cell membranes, causing systemic vasodilation and reduced cardiac afterload.',
      dosage: {
        standard: '5 mg once daily (OD)',
        maximum: '10 mg/day',
        frequency: 'Once daily, preferably at the same time each morning',
        route: 'Oral',
        withFood: false,
        withWater: true,
        missedDose:
          'Take as soon as remembered on the same day. Skip if next dose is due within 12 hours. Never double up.',
        overdoseWarning:
          'Severe hypotension and reflex tachycardia. Seek emergency care immediately.',
      },
      sideEffects: [
        {
          id: 'se-005',
          name: 'Peripheral Oedema',
          description:
            'Ankle and foot swelling from vasodilation — most common side effect; dose-dependent.',
          severity: 'moderate',
          frequency: 'common',
        },
        {
          id: 'se-006',
          name: 'Headache',
          description: 'Dull pulsatile headache, especially in the first weeks of therapy.',
          severity: 'low',
          frequency: 'common',
        },
        {
          id: 'se-007',
          name: 'Facial Flushing',
          description: 'Warmth and redness of face due to cutaneous vasodilation.',
          severity: 'low',
          frequency: 'common',
        },
        {
          id: 'se-008',
          name: 'Palpitations',
          description: 'Reflex sympathetic activation may cause awareness of heartbeat.',
          severity: 'moderate',
          frequency: 'uncommon',
          actionRequired: 'Report persistent palpitations or irregular rhythm to your doctor promptly.',
        },
        {
          id: 'se-009',
          name: 'Gingival Hyperplasia',
          description: 'Overgrowth of gum tissue with long-term use; rare.',
          severity: 'moderate',
          frequency: 'rare',
          actionRequired: 'Maintain good dental hygiene; inform dentist of medication.',
        },
      ],
      interactions: [
        {
          id: 'int-003',
          drugName: 'Simvastatin',
          severity: 'moderate',
          description:
            'Amlodipine inhibits CYP3A4, increasing simvastatin plasma concentrations and myopathy risk.',
          recommendation: 'Limit simvastatin dose to 20 mg/day when co-administered with amlodipine.',
        },
        {
          id: 'int-004',
          drugName: 'Cyclosporine',
          severity: 'high',
          description: 'May significantly elevate cyclosporine blood levels via CYP3A4 inhibition.',
          recommendation: 'Frequent monitoring of cyclosporine trough levels required.',
        },
      ],
      drowsinessLevel: 'mild',
      ageWarnings: [
        {
          ageGroup: 'geriatric',
          warning:
            'Elderly patients are more susceptible to hypotension and falls. Initiate at lower dose.',
          contraindicated: false,
          adjustedDose: 'Start at 2.5 mg OD and titrate carefully.',
        },
      ],
      lifestyleRecommendations: [
        {
          id: 'lr-004',
          category: 'diet',
          section: 'bestPractice' as const,
          title: 'Reduce Sodium Intake',
          description:
            'Limit dietary sodium to <2 g/day (no added salt) to maximise blood pressure control.',
          severity: 'moderate',
        },
        {
          id: 'lr-005',
          category: 'activity',
          section: 'supportive' as const,
          title: 'Daily BP Monitoring',
          description:
            'Measure blood pressure twice daily (morning and evening) and keep a log to share with your doctor.',
          severity: 'low',
        },
        {
          id: 'lr-006',
          category: 'driving',
          section: 'avoid' as const,
          title: 'Caution When Driving',
          description:
            'Mild dizziness possible, especially when rising from sitting or lying positions (orthostatic hypotension).',
          severity: 'moderate',
        },
      ],
      todaysPrecautions: [
        { id: 'tp-aml-1', emoji: '🍊', text: 'Avoid grapefruit juice — it raises Amlodipine blood levels unpredictably.', severity: 'high' as const },
        { id: 'tp-aml-2', emoji: '🚗', text: 'Mild dizziness is possible; avoid driving if you feel light-headed.', severity: 'moderate' as const },
        { id: 'tp-aml-3', emoji: '💊', text: "Do not skip today's dose of Amlodipine; take it at the same time each morning.", severity: 'moderate' as const },
        { id: 'tp-aml-4', emoji: '💧', text: 'Drink plenty of water and rise slowly from sitting or lying positions.', severity: 'low' as const },
        { id: 'tp-aml-5', emoji: '🧂', text: 'Reduce salt in your meals today to support blood pressure control.', severity: 'low' as const },
      ],
      requiresPrescription: true,
      storageInstructions: 'Store below 30°C in original packaging; keep away from moisture.',
    },
    {
      id: 'med-003',
      name: 'Alprazolam',
      genericName: 'Alprazolam',
      brandNames: ['Xanax', 'Alprax', 'Restyl', 'Trika'],
      drugClass: 'Benzodiazepine / Anxiolytic–Sedative',
      indication: 'Anxiety Disorders, Insomnia (short-term)',
      description:
        'Alprazolam is a short-acting benzodiazepine that produces rapid anxiolytic and sedative effects by enhancing GABA activity. It is a Schedule H1 controlled substance due to significant abuse and dependence potential.',
      mechanism:
        'Positive allosteric modulator of GABA-A receptors; increases chloride conductance, producing CNS depression, muscle relaxation, and anxiolysis.',
      dosage: {
        standard: '0.25 mg at bedtime (HS)',
        maximum: '4 mg/day (anxiety); 10 mg/day in exceptional cases under supervision',
        frequency: 'Once at bedtime — short-term use only (maximum 2–4 weeks)',
        route: 'Oral',
        withFood: false,
        withWater: true,
        missedDose:
          'Skip the missed bedtime dose entirely if it is morning. Do not take extra to compensate.',
        overdoseWarning:
          'CNS and respiratory depression — confusion, slurred speech, loss of consciousness, respiratory arrest. Flumazenil is the antidote. Call emergency services immediately.',
      },
      sideEffects: [
        {
          id: 'se-010',
          name: 'Drowsiness / Sedation',
          description:
            'Profound sedation, especially at initiation; residual next-morning grogginess common.',
          severity: 'high',
          frequency: 'common',
        },
        {
          id: 'se-011',
          name: 'Cognitive Impairment',
          description:
            'Short-term memory deficits, reduced concentration, and slowed psychomotor response.',
          severity: 'moderate',
          frequency: 'common',
          actionRequired: 'Avoid tasks requiring full mental alertness the morning after use.',
        },
        {
          id: 'se-012',
          name: 'Physical Dependence',
          description:
            'Physiological dependence develops within 2–4 weeks; withdrawal can be severe and life-threatening.',
          severity: 'critical',
          frequency: 'common',
          actionRequired:
            'Never stop abruptly. Taper dose gradually under medical supervision. Report any withdrawal symptoms (sweating, tremors, seizures) immediately.',
        },
        {
          id: 'se-013',
          name: 'Respiratory Depression',
          description: 'Dangerously reduced breathing rate, especially combined with other CNS depressants.',
          severity: 'critical',
          frequency: 'rare',
          actionRequired:
            'Seek emergency care immediately if difficulty breathing or unusual drowsiness occurs.',
        },
        {
          id: 'se-014',
          name: 'Paradoxical Excitation',
          description:
            'Rare — increased anxiety, agitation, or aggression, particularly in elderly patients.',
          severity: 'moderate',
          frequency: 'rare',
          actionRequired: 'Report to doctor; discontinuation under supervision may be required.',
        },
      ],
      interactions: [
        {
          id: 'int-005',
          drugName: 'Alcohol',
          severity: 'critical',
          description:
            'Synergistic CNS and respiratory depression — combination can be fatal even at therapeutic doses.',
          recommendation:
            'Absolutely contraindicated. Do not consume any alcohol while taking Alprazolam.',
        },
        {
          id: 'int-006',
          drugName: 'Opioid Analgesics',
          severity: 'critical',
          description:
            'Combined use multiplies overdose and respiratory arrest risk — a leading cause of drug-related deaths.',
          recommendation:
            'Avoid concurrent use. If unavoidable, use lowest effective doses under close clinical monitoring.',
        },
        {
          id: 'int-007',
          drugName: 'Ketoconazole / Itraconazole',
          severity: 'high',
          description:
            'Strong CYP3A4 inhibitors markedly elevate alprazolam plasma levels increasing toxicity risk.',
          recommendation: 'Avoid combination; if essential, reduce alprazolam dose substantially.',
        },
      ],
      drowsinessLevel: 'severe',
      controlledSubstance: true,
      ageWarnings: [
        {
          ageGroup: 'geriatric',
          warning:
            'High risk of falls, hip fractures, and cognitive decline. Paradoxical agitation possible. Beers Criteria: Avoid in elderly.',
          contraindicated: false,
          adjustedDose: 'Use lowest possible dose for shortest duration only; consider alternatives.',
        },
        {
          ageGroup: 'pediatric',
          warning: 'Not approved for anxiety or insomnia in patients under 18 years.',
          contraindicated: true,
        },
      ],
      lifestyleRecommendations: [
        {
          id: 'lr-007',
          category: 'driving',
          section: 'avoid' as const,
          title: 'Do NOT Drive',
          description:
            'Alprazolam causes severe sedation and impaired reaction time. Absolutely do not drive or operate machinery.',
          severity: 'critical',
        },
        {
          id: 'lr-008',
          category: 'alcohol',
          section: 'avoid' as const,
          title: 'Zero Alcohol — Strictly',
          description:
            'Combining benzodiazepines with alcohol is potentially fatal. No exceptions.',
          severity: 'critical',
        },
        {
          id: 'lr-009',
          category: 'sleep',
          section: 'bestPractice' as const,
          title: 'Consistent Sleep Schedule',
          description:
            'Take only at the prescribed bedtime. Irregular use increases dependence risk and disrupts sleep architecture.',
          severity: 'high',
        },
        {
          id: 'lr-010',
          category: 'other',
          section: 'bestPractice' as const,
          title: 'Short-Term Use Only',
          description:
            'This prescription is for 10 days only. Do not refill without doctor consultation. Discuss long-term anxiety management strategies.',
          severity: 'high',
        },
      ],
      todaysPrecautions: [
        { id: 'tp-alp-1', emoji: '🚫', text: 'Absolutely no alcohol — combining Alprazolam with alcohol can be fatal.', severity: 'critical' as const },
        { id: 'tp-alp-2', emoji: '🚗', text: 'Do NOT drive or operate machinery — Alprazolam causes significant sedation.', severity: 'critical' as const },
        { id: 'tp-alp-3', emoji: '⚠️', text: 'Do not stop abruptly — always taper under medical supervision to avoid seizures.', severity: 'critical' as const },
        { id: 'tp-alp-4', emoji: '💊', text: 'Take only the prescribed dose at bedtime — never increase the dose yourself.', severity: 'high' as const },
        { id: 'tp-alp-5', emoji: '🍊', text: 'Avoid grapefruit juice — it increases Alprazolam levels in your blood.', severity: 'high' as const },
        { id: 'tp-alp-6', emoji: '💧', text: 'Stay hydrated and maintain a regular sleep schedule during this course.', severity: 'low' as const },
      ],
      requiresPrescription: true,
      storageInstructions:
        'Store at room temperature (15–30°C). Keep away from children. Controlled substance — secure storage required. Do not share with others.',
    },
  ],
}
