import { z } from 'zod';

/** Validates a non-empty, non-whitespace research topic string. */
export const topicSchema = z.object({
  topic: z
    .string()
    .min(1, 'Topic is required')
    .refine((val) => val.trim().length > 0, 'Topic cannot be blank'),
});

export type TopicFormValues = z.infer<typeof topicSchema>;

/** Validates run constraint overrides with cross-field business rules. */
export const constraintsSchema = z
  .object({
    year_from: z
      .number()
      .int()
      .min(1900, 'Year must be 1900 or later')
      .max(new Date().getFullYear(), 'Year cannot be in the future'),
    year_to: z
      .number()
      .int()
      .min(1900, 'Year must be 1900 or later')
      .max(new Date().getFullYear() + 1, 'Year cannot be too far in the future'),
    open_access_only: z.boolean(),
    max_selected_papers: z
      .number()
      .int()
      .min(1, 'Must select at least 1 paper')
      .max(100, 'Cannot select more than 100 papers'),
    novelty_weight: z
      .number()
      .min(0, 'Weight must be between 0 and 1')
      .max(1, 'Weight must be between 0 and 1'),
    feasibility_weight: z
      .number()
      .min(0, 'Weight must be between 0 and 1')
      .max(1, 'Weight must be between 0 and 1'),
    lab_mode: z.enum(['wet', 'dry', 'either']),
  })
  .refine((data) => data.year_from <= data.year_to, {
    message: 'year_from must be less than or equal to year_to',
    path: ['year_from'],
  })
  .refine(
    (data) => {
      const sum = Math.round((data.novelty_weight + data.feasibility_weight) * 100) / 100;
      return sum === 1.0;
    },
    {
      message: 'novelty_weight + feasibility_weight must equal 1.0',
      path: ['novelty_weight'],
    },
  );

export type ConstraintsFormValues = z.infer<typeof constraintsSchema>;
