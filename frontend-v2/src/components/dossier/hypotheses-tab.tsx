'use client';

import { Lightbulb } from 'lucide-react';
import { Card, Badge, Progress } from '@/components/primitives';
import { cn } from '@/lib/utils';
import type { Hypothesis, EvidenceCard } from '@/types';

interface HypothesesTabProps {
  hypotheses: Hypothesis[];
  evidence: EvidenceCard[];
}

export function HypothesesTab({ hypotheses, evidence }: HypothesesTabProps) {
  const getEvidenceById = (id: string) => evidence.find((e) => e.evidence_id === id);

  if (hypotheses.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-8 text-center">
        <Lightbulb className="mx-auto h-12 w-12 text-gray-300" />
        <p className="mt-2 text-gray-500">No hypotheses generated for this run.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Generated Hypotheses</h3>
        <span className="text-sm text-gray-500">{hypotheses.length} hypotheses</span>
      </div>

      <div className="space-y-4">
        {hypotheses
          .sort((a, b) => a.rank - b.rank)
          .map((hypothesis) => (
            <Card key={hypothesis.rank} className="p-6">
              <div className="flex items-start gap-4">
                <div
                  className={cn(
                    'flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full font-bold text-white',
                    hypothesis.rank === 1
                      ? 'bg-amber-500'
                      : hypothesis.rank === 2
                      ? 'bg-gray-400'
                      : 'bg-amber-700'
                  )}
                >
                  {hypothesis.rank}
                </div>
                <div className="min-w-0 flex-1">
                  <h4 className="text-lg font-semibold text-gray-900">
                    {hypothesis.title}
                  </h4>
                  <p className="mt-2 text-gray-700">{hypothesis.hypothesis_statement}</p>

                  {/* Scores */}
                  <div className="mt-4 grid gap-4 sm:grid-cols-3">
                    <div>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="text-gray-600">Novelty</span>
                        <span className="font-medium">
                          {(hypothesis.novelty_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <Progress value={hypothesis.novelty_score * 100} />
                    </div>
                    <div>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="text-gray-600">Feasibility</span>
                        <span className="font-medium">
                          {(hypothesis.feasibility_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <Progress value={hypothesis.feasibility_score * 100} />
                    </div>
                    <div>
                      <div className="mb-1 flex items-center justify-between text-sm">
                        <span className="text-gray-600">Overall</span>
                        <span className="font-medium">
                          {(hypothesis.overall_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <Progress value={hypothesis.overall_score * 100} />
                    </div>
                  </div>

                  {/* Why plausible */}
                  <div className="mt-4">
                    <h5 className="text-sm font-medium text-gray-700">Why Plausible</h5>
                    <p className="mt-1 text-sm text-gray-600">{hypothesis.why_plausible}</p>
                  </div>

                  {/* Prediction */}
                  <div className="mt-4">
                    <h5 className="text-sm font-medium text-gray-700">Prediction</h5>
                    <p className="mt-1 text-sm text-gray-600">{hypothesis.prediction}</p>
                  </div>

                  {/* Evidence grounding */}
                  <div className="mt-4">
                    <h5 className="text-sm font-medium text-gray-700">Evidence Grounding</h5>
                    <div className="mt-2 flex flex-wrap gap-1">
                      {hypothesis.supporting_evidence_ids.slice(0, 5).map((id) => {
                        const ev = getEvidenceById(id);
                        return (
                          <Badge key={id} variant="success" className="text-xs">
                            {ev?.title ?? id.slice(0, 8)}
                          </Badge>
                        );
                      })}
                      {hypothesis.supporting_evidence_ids.length > 5 && (
                        <Badge variant="secondary" className="text-xs">
                          +{hypothesis.supporting_evidence_ids.length - 5} more
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Minimal Experiment */}
                  {hypothesis.minimal_experiment && (
                    <div className="mt-4 rounded-lg bg-gray-50 p-4">
                      <h5 className="text-sm font-medium text-gray-700">Minimal Experiment</h5>
                      <div className="mt-2 space-y-2 text-sm text-gray-600">
                        <div>
                          <span className="font-medium text-gray-700">System: </span>
                          {hypothesis.minimal_experiment.system}
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Design: </span>
                          {hypothesis.minimal_experiment.design}
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Control: </span>
                          {hypothesis.minimal_experiment.control}
                        </div>
                        {hypothesis.minimal_experiment.readouts.length > 0 && (
                          <div>
                            <span className="font-medium text-gray-700">Readouts: </span>
                            {hypothesis.minimal_experiment.readouts.join(', ')}
                          </div>
                        )}
                        <div>
                          <span className="font-medium text-gray-700">Success Criteria: </span>
                          {hypothesis.minimal_experiment.success_criteria}
                        </div>
                        <div>
                          <span className="font-medium text-gray-700">Failure Interpretation: </span>
                          {hypothesis.minimal_experiment.failure_interpretation}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Risks */}
                  {hypothesis.risks.length > 0 && (
                    <div className="mt-4">
                      <h5 className="text-sm font-medium text-gray-700">Risks</h5>
                      <ul className="mt-1 list-inside list-disc space-y-1 text-sm text-gray-600">
                        {hypothesis.risks.slice(0, 3).map((risk, i) => (
                          <li key={i}>{risk}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
      </div>
    </div>
  );
}
