'use server';

/**
 * @fileOverview This file defines a Genkit flow for analyzing and scoring photos based on various criteria.
 *
 * The flow takes a photo (as a data URI) as input and returns an AI score and duplicate file detection.
 * - aiScorePhotos - The main function to initiate the photo scoring process.
 * - AIScorePhotosInput - The input type for the aiScorePhotos function.
 * - AIScorePhotosOutput - The output type for the aiScorePhotos function.
 */

import {ai} from '../genkit.js';
import {z} from 'genkit';

const AIScorePhotosInputSchema = z.object({
  photoDataUri: z
    .string()
    .describe(
      'A photo as a data URI that must include a MIME type and use Base64 encoding. Expected format: \'data:<mimetype>;base64,<encoded_data>\'.'
    ),
});
export type AIScorePhotosInput = z.infer<typeof AIScorePhotosInputSchema>;

const AIScorePhotosOutputSchema = z.object({
  aiScore: z
    .number()
    .min(0)
    .max(100)
    .describe('The AI score of the photo, ranging from 0 to 100.'),
  isDuplicate: z.boolean().describe('Whether the photo is a duplicate.'),
});
export type AIScorePhotosOutput = z.infer<typeof AIScorePhotosOutputSchema>;

export async function aiScorePhotos(input: AIScorePhotosInput): Promise<AIScorePhotosOutput> {
  return aiScorePhotosFlow(input);
}

const aiScorePhotosPrompt = ai.definePrompt({
  name: 'aiScorePhotosPrompt',
  input: {schema: AIScorePhotosInputSchema},
  output: {schema: AIScorePhotosOutputSchema},
  prompt: `You are an AI photo analysis expert. Analyze the provided photo and provide an AI score from 0 to 100, where 100 is a perfect photo.

Consider these criteria when determining the score:
- Sharpness: Is the photo in focus? Are there any blur issues?
- Exposure: Is the photo properly exposed? Is it too bright or too dark?
- Noise: Is there excessive noise (high ISO)?
- Face Detection: If there are faces, are the eyes open, in focus, and showing good expression?
- Composition: Is the composition good? (e.g., horizon straight, rule of thirds)
- Duplicate Detection: Is this photo likely a duplicate of another photo?

Based on your analysis, provide an overall AI score and indicate whether the photo is a duplicate.

Photo: {{media url=photoDataUri}}

Please output a valid JSON:
{{output schema=AIScorePhotosOutputSchema}}
`,
});

const aiScorePhotosFlow = ai.defineFlow(
  {
    name: 'aiScorePhotosFlow',
    inputSchema: AIScorePhotosInputSchema,
    outputSchema: AIScorePhotosOutputSchema,
  },
  async input => {
    const {output} = await aiScorePhotosPrompt(input);
    return output!;
  }
);
