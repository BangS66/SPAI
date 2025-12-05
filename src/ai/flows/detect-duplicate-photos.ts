'use server';

/**
 * @fileOverview Flow to detect duplicate or similar photos.
 *
 * - detectDuplicatePhotos - A function that handles the detection of duplicate or similar photos.
 * - DetectDuplicatePhotosInput - The input type for the detectDuplicatePhotos function.
 * - DetectDuplicatePhotosOutput - The return type for the detectDuplicatePhotos function.
 */

import {ai} from '../genkit.js';
import {z} from 'genkit';

const DetectDuplicatePhotosInputSchema = z.object({
  photoDataUri: z
    .string()
    .describe(
      "A photo to check for duplicates, as a data URI that must include a MIME type and use Base64 encoding. Expected format: 'data:<mimetype>;base64,<encoded_data>'."
    ),
  otherPhotoDataUris: z
    .array(z.string())
    .describe(
      "An array of photo data URIs to compare against the main photo, each must include a MIME type and use Base64 encoding. Expected format: 'data:<mimetype>;base64,<encoded_data>'."
    ),
});
export type DetectDuplicatePhotosInput = z.infer<typeof DetectDuplicatePhotosInputSchema>;

const DetectDuplicatePhotosOutputSchema = z.object({
  isDuplicate: z.boolean().describe('Whether the photo is a duplicate of any in the comparison set.'),
  similarityScores: z
    .array(z.number())
    .describe('An array of similarity scores (0-1) for each photo in the comparison set.'),
});
export type DetectDuplicatePhotosOutput = z.infer<typeof DetectDuplicatePhotosOutputSchema>;

export async function detectDuplicatePhotos(input: DetectDuplicatePhotosInput): Promise<DetectDuplicatePhotosOutput> {
  return detectDuplicatePhotosFlow(input);
}

const prompt = ai.definePrompt({
  name: 'detectDuplicatePhotosPrompt',
  input: {schema: DetectDuplicatePhotosInputSchema},
  output: {schema: DetectDuplicatePhotosOutputSchema},
  prompt: `You are an AI expert in image analysis. Given a photo and a list of other photos, determine if the photo is a duplicate or very similar to any of the others.

  Respond with whether the image is a duplicate, and a similarity score (0-1) for each photo in the otherPhotosDataUris array. The similarity score should quantify how similar the image is to the image at the index in the array.

Photo: {{media url=photoDataUri}}
Other Photos:
{{#each otherPhotoDataUris}}
  - {{media url=this}}
{{/each}}`,
});

const detectDuplicatePhotosFlow = ai.defineFlow(
  {
    name: 'detectDuplicatePhotosFlow',
    inputSchema: DetectDuplicatePhotosInputSchema,
    outputSchema: DetectDuplicatePhotosOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
