"use server";

import { z } from "zod";

const scoreSchema = z.object({
  photoDataUri: z.string().refine(val => val.startsWith('data:image/'), {
    message: "Must be a valid data URI for an image.",
  }),
});

export async function getAiScore(input: { photoDataUri: string }): Promise<{ aiScore: number, isDuplicate?: boolean } | null> {
  const validation = scoreSchema.safeParse(input);
  if (!validation.success) {
    console.error("Invalid input for getAiScore:", validation.error.flatten());
    return null;
  }

  // Placeholder logic: Generate a random score for demonstration
  const randomScore = Math.floor(Math.random() * 51) + 50; // Score between 50 and 100
  const isDuplicate = Math.random() > 0.8; // 20% chance of being a duplicate

  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 500));

  return {
    aiScore: randomScore,
    isDuplicate: isDuplicate,
  };
}
