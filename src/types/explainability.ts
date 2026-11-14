export interface ShapFeatureWeight {
  id: string;
  name: string;
  displayValue: string;
  weightPercentage: number;
  isPositive: boolean;
  barWidthPercentage: number;
  detailNote?: string;
}

export interface FairnessRegionData {
  regionName: string;
  approvalRate: number;
  parityPercentage: number;
  auditedSampleCount: number;
}

export interface ScholarshipEvaluationDossier {
  expedienteId: string;
  applicantName: string;
  academicRecordId: string;
  major: string;
  score: number;
  maxScore: number;
  minimumThreshold: number;
  verdictLabel: string;
  aiVerdict: string;
  humanAuditorVerdict: string;
  concordanceLabel: string;
  impactDisparityRatio: string;
  parityBadgeText: string;
  variables: ShapFeatureWeight[];
  regions: FairnessRegionData[];
}
