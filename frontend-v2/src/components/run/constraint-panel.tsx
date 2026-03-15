'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Settings2 } from 'lucide-react';
import { Button, Input } from '@/components/primitives';
import { defaultConstraints, type RunConstraints } from '@/types';

interface ConstraintPanelProps {
  constraints: RunConstraints;
  onChange: (constraints: RunConstraints) => void;
}

export function ConstraintPanel({ constraints, onChange }: ConstraintPanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const updateConstraint = <K extends keyof RunConstraints>(
    key: K,
    value: RunConstraints[K]
  ) => {
    onChange({ ...constraints, [key]: value });
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-2">
          <Settings2 className="h-5 w-5 text-gray-500" />
          <span className="font-medium text-gray-700">Advanced Constraints</span>
        </div>
        {isOpen ? (
          <ChevronUp className="h-5 w-5 text-gray-400" />
        ) : (
          <ChevronDown className="h-5 w-5 text-gray-400" />
        )}
      </button>

      {isOpen && (
        <div className="space-y-4 border-t border-gray-200 p-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-600">
                Year From
              </label>
              <Input
                type="number"
                value={constraints.year_from}
                onChange={(e) => updateConstraint('year_from', parseInt(e.target.value))}
                min={2000}
                max={2030}
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-600">
                Year To
              </label>
              <Input
                type="number"
                value={constraints.year_to}
                onChange={(e) => updateConstraint('year_to', parseInt(e.target.value))}
                min={2000}
                max={2030}
              />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-gray-600">
              Max Papers
            </label>
            <Input
              type="number"
              value={constraints.max_selected_papers}
              onChange={(e) => updateConstraint('max_selected_papers', parseInt(e.target.value))}
              min={12}
              max={60}
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={constraints.open_access_only}
                onChange={(e) => updateConstraint('open_access_only', e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-gray-600">Open Access Only</span>
            </label>
          </div>

          <div className="flex gap-2">
            {(['wet', 'dry', 'either'] as const).map((mode) => (
              <Button
                key={mode}
                type="button"
                variant={constraints.lab_mode === mode ? 'default' : 'outline'}
                size="sm"
                onClick={() => updateConstraint('lab_mode', mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)} Lab
              </Button>
            ))}
          </div>

          <div className="flex justify-end">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => onChange(defaultConstraints)}
            >
              Reset to Defaults
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
