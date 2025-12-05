"use client";

import React, { useState, useReducer, useEffect, useCallback, useRef } from "react";
import { getAiScore } from "@/app/actions";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  FileUp,
  FolderUp,
  RotateCcw,
  RotateCw,
  Sparkles,
  Undo2,
  XCircle,
  FileText,
} from "lucide-react";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useToast } from "@/hooks/use-toast";

type PhotoStatus = "pending" | "scoring" | "scored" | "sorted" | "error";
type SortDestination = "sortir_1" | "sortir_2" | "sortir_3" | "rejected";
type AutoSortDestination = "Best" | "Good" | "Reject";

interface Photo {
  id: string;
  file: File;
  dataUri: string;
  name: string;
  aiScore?: number;
  isDuplicate?: boolean;
  status: PhotoStatus;
  sortedTo?: SortDestination;
  rotation: number;
}

interface State {
  photos: Photo[];
  history: number[];
}

type Action =
  | { type: "ADD_PHOTOS"; payload: Photo[] }
  | { type: "START_SCORING"; payload: { id: string } }
  | { type: "UPDATE_SCORE"; payload: { id: string; score: number; isDuplicate: boolean } }
  | { type: "SORT_PHOTO"; payload: { index: number; destination: SortDestination } }
  | { type: "UNDO" }
  | { type: "ROTATE"; payload: { index: number; direction: "cw" | "ccw" } }
  | { type: "RESET" };

const initialState: State = { photos: [], history: [] };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "ADD_PHOTOS":
      return { ...initialState, photos: action.payload };
    case "START_SCORING":
      return {
        ...state,
        photos: state.photos.map(p => p.id === action.payload.id ? { ...p, status: 'scoring' } : p),
      };
    case "UPDATE_SCORE":
      return {
        ...state,
        photos: state.photos.map(p =>
          p.id === action.payload.id
            ? { ...p, status: 'scored', aiScore: action.payload.score, isDuplicate: action.payload.isDuplicate }
            : p
        ),
      };
    case "SORT_PHOTO": {
      const { index, destination } = action.payload;
      const newPhotos = [...state.photos];
      if (newPhotos[index]) {
        newPhotos[index] = { ...newPhotos[index], status: 'sorted', sortedTo: destination };
      }
      return { ...state, photos: newPhotos, history: [...state.history, index] };
    }
    case "UNDO": {
      if (state.history.length === 0) return state;
      const lastActionIndex = state.history[state.history.length - 1];
      const newPhotos = [...state.photos];
      if (newPhotos[lastActionIndex]) {
        const { sortedTo, ...rest } = newPhotos[lastActionIndex];
        newPhotos[lastActionIndex] = { ...rest, status: 'scored' };
      }
      return { ...state, photos: newPhotos, history: state.history.slice(0, -1) };
    }
    case "ROTATE": {
        const { index, direction } = action.payload;
        const newPhotos = [...state.photos];
        if (newPhotos[index]) {
            const currentRotation = newPhotos[index].rotation;
            const newRotation = direction === 'cw' ? (currentRotation + 90) % 360 : (currentRotation - 90 + 360) % 360;
            newPhotos[index] = { ...newPhotos[index], rotation: newRotation };
        }
        return { ...state, photos: newPhotos };
    }
    case "RESET":
        return initialState;
    default:
      return state;
  }
}

const readFileAsDataURL = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
};

const getAutoSortFolder = (score: number | undefined): AutoSortDestination => {
    if (score === undefined) return "Reject";
    if (score >= 80) return "Best";
    if (score >= 60) return "Good";
    return "Reject";
};

export function SpaiClient() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const [mode, setMode] = useState<"manual" | "ai">("manual");
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0);
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { photos, history } = state;
  const currentPhoto = photos[currentPhotoIndex];
  const unscoredPhotos = photos.filter(p => p.status === 'pending');
  const unsortedPhotos = photos.filter(p => p.status === 'scored' || p.status === 'error');

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    setIsLoading(true);
    setProgress(0);
    const files = Array.from(e.target.files).filter(file => file.type.startsWith("image/"));

    const photoPromises = files.map(async (file, index) => ({
        id: `${file.name}-${index}`,
        file,
        dataUri: await readFileAsDataURL(file),
        name: file.name,
        status: 'pending' as PhotoStatus,
        rotation: 0,
    }));

    const newPhotos = await Promise.all(photoPromises);
    dispatch({ type: "ADD_PHOTOS", payload: newPhotos });
    setCurrentPhotoIndex(0);
    setIsLoading(false);
    toast({ title: "Photos Loaded", description: `${newPhotos.length} photos are ready for analysis.` });
  };

  const runAiAnalysis = async () => {
    if (unscoredPhotos.length === 0) {
        toast({ title: "All photos are already scored!", variant: "default" });
        return;
    }
    setIsLoading(true);
    setProgress(0);

    for (let i = 0; i < unscoredPhotos.length; i++) {
        const photo = unscoredPhotos[i];
        dispatch({ type: "START_SCORING", payload: { id: photo.id } });
        const result = await getAiScore({ photoDataUri: photo.dataUri });

        if (result && typeof result.aiScore === 'number') {
            dispatch({ type: "UPDATE_SCORE", payload: { id: photo.id, score: result.aiScore, isDuplicate: result.isDuplicate || false } });
        } else {
             dispatch({ type: "UPDATE_SCORE", payload: { id: photo.id, score: 0, isDuplicate: false } }); // Mark as error
        }
        setProgress(((i + 1) / unscoredPhotos.length) * 100);
    }

    setIsLoading(false);
    toast({ title: "AI Analysis Complete", description: "All photos have been scored." });
  };

  const navigate = useCallback((direction: "next" | "prev") => {
      const sortedOrSkippedIndices = new Set(photos.map((p, i) => p.status === 'sorted' ? i : -1).filter(i => i !== -1));
      let nextIndex = currentPhotoIndex;
      const total = photos.length;

      const findNext = (start: number, dir: 1 | -1) => {
          let i = (start + dir + total) % total;
          while (i !== start) {
              if (!sortedOrSkippedIndices.has(i)) return i;
              i = (i + dir + total) % total;
          }
          return -1; // No unsorted photos left
      };

      if(direction === 'next') {
          nextIndex = findNext(currentPhotoIndex, 1);
      } else {
          nextIndex = findNext(currentPhotoIndex, -1);
      }

      if(nextIndex !== -1) {
          setCurrentPhotoIndex(nextIndex);
      } else {
        toast({ title: "All photos sorted!", description: "You can find them in the AI Mode tab or export the results." });
      }
  }, [currentPhotoIndex, photos, toast]);


  const handleSort = useCallback((destination: SortDestination) => {
    if (!currentPhoto || currentPhoto.status !== 'scored') {
        toast({ title: "Photo not scored yet", description: "Please run AI analysis before sorting.", variant: "destructive" });
        return;
    };
    dispatch({ type: "SORT_PHOTO", payload: { index: currentPhotoIndex, destination } });
    navigate("next");
  }, [currentPhoto, currentPhotoIndex, navigate, toast]);

  const handleUndo = useCallback(() => {
    if (history.length === 0) return;
    const lastSortedPhotoIndex = history[history.length - 1];
    dispatch({ type: "UNDO" });
    setCurrentPhotoIndex(lastSortedPhotoIndex);
    toast({ title: "Undo Successful", description: "Last sorting action has been reverted." });
  }, [history]);

  const handleRotate = (direction: 'cw' | 'ccw') => {
      if(!currentPhoto) return;
      dispatch({ type: 'ROTATE', payload: { index: currentPhotoIndex, direction }});
  };

  const handleExport = () => {
    if(photos.length === 0) {
        toast({ title: "No data to export", variant: "destructive"});
        return;
    }
    const header = "filename,ai_score,is_duplicate,manual_sort_folder,ai_sort_folder\n";
    const rows = photos.map(p => {
        const aiFolder = getAutoSortFolder(p.aiScore);
        return `${p.name},${p.aiScore ?? 'N/A'},${p.isDuplicate ?? 'N/A'},${p.sortedTo ?? 'N/A'},${aiFolder}`;
    }).join("\n");

    const csvContent = header + rows;
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", "spai_results.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast({ title: "Export Successful", description: "CSV file has been downloaded." });
  };


  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isLoading || photos.length === 0 || mode !== 'manual') return;

      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      switch (e.key.toLowerCase()) {
        case "arrowright": navigate("next"); break;
        case "arrowleft": navigate("prev"); break;
        case "1": handleSort("sortir_1"); break;
        case "2": handleSort("sortir_2"); break;
        case "3": handleSort("sortir_3"); break;
        case "x": handleSort("rejected"); break;
        case "s": navigate("next"); break;
        case "z": handleUndo(); break;
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isLoading, photos.length, mode, navigate, handleSort, handleUndo]);

  if (photos.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-4">
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold text-primary">Welcome to SPAI</h1>
          <p className="text-muted-foreground max-w-md mx-auto">Smart Photo AI to sort, select, and rate your photos. Start by choosing a folder.</p>
          <Button size="lg" onClick={() => fileInputRef.current?.click()}>
            <FolderUp className="mr-2 h-5 w-5" />
            Choose Folder
          </Button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            className="hidden"
            multiple
          />
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex flex-col h-full max-h-screen overflow-hidden">
        <header className="flex-shrink-0 flex items-center justify-between p-2 md:p-4 border-b">
            <div className="flex items-center gap-4">
                 <Button variant="outline" size="sm" onClick={() => {
                     dispatch({ type: 'RESET'});
                     if(fileInputRef.current) fileInputRef.current.value = "";
                 }}>
                    <FolderUp className="mr-2 h-4 w-4" />
                    New Folder
                </Button>
                <Tabs value={mode} onValueChange={(value) => setMode(value as "manual" | "ai")} className="w-auto">
                    <TabsList>
                        <TabsTrigger value="manual">Manual Mode</TabsTrigger>
                        <TabsTrigger value="ai">AI Mode</TabsTrigger>
                    </TabsList>
                </Tabs>
            </div>
            <div className="flex items-center gap-2">
                <Button size="sm" onClick={runAiAnalysis} disabled={isLoading || unscoredPhotos.length === 0}>
                    <Sparkles className="mr-2 h-4 w-4" />
                    {isLoading ? "Analyzing..." : `Analyze ${unscoredPhotos.length} Photos`}
                </Button>
                 <Button size="sm" variant="secondary" onClick={handleExport}>
                    <FileText className="mr-2 h-4 w-4" />
                    Export CSV
                </Button>
            </div>
        </header>

        {isLoading && <Progress value={progress} className="w-full h-1" />}

        <main className="flex-1 overflow-auto">
            <TabsContent value="manual" className="h-full mt-0">
                {currentPhoto ? (
                <div className="grid grid-cols-1 lg:grid-cols-4 h-full">
                    <div className="lg:col-span-3 bg-background/50 flex items-center justify-center p-4 relative overflow-hidden">
                        <Image
                            src={currentPhoto.dataUri}
                            alt={currentPhoto.name}
                            fill
                            className="object-contain"
                            style={{ transform: `rotate(${currentPhoto.rotation}deg)` }}
                        />
                         <div className="absolute top-4 right-4 flex gap-2">
                            <Button variant="outline" size="icon" onClick={() => handleRotate('ccw')}><RotateCcw /></Button>
                            <Button variant="outline" size="icon" onClick={() => handleRotate('cw')}><RotateCw /></Button>
                        </div>
                        <div className="absolute bottom-4 left-4 flex gap-2">
                            <Button variant="outline" size="icon" onClick={() => navigate('prev')}><ArrowLeft /></Button>
                            <Button variant="outline" size="icon" onClick={() => navigate('next')}><ArrowRight /></Button>
                        </div>
                    </div>
                    <div className="lg:col-span-1 border-l bg-card p-4 flex flex-col gap-4 overflow-y-auto">
                        <h2 className="text-lg font-semibold truncate">{currentPhoto.name}</h2>

                        <div className="space-y-2">
                            <h3 className="font-medium">AI Score</h3>
                            {currentPhoto.status === 'scored' || currentPhoto.status === 'sorted' ? (
                                <div className="flex items-baseline gap-2">
                                <span className="text-5xl font-bold text-primary">{currentPhoto.aiScore}</span>
                                <span className="text-xl text-muted-foreground">/ 100</span>
                                {currentPhoto.isDuplicate && <Badge variant="destructive">Similar</Badge>}
                                </div>
                            ) : (
                                <p className="text-muted-foreground">Not scored yet.</p>
                            )}
                        </div>

                        <div className="space-y-2">
                             <h3 className="font-medium">Actions</h3>
                             <div className="grid grid-cols-2 gap-2">
                                <Button variant="outline" onClick={() => handleSort('sortir_1')}><span className="mr-auto">Sort 1</span><Badge>1</Badge></Button>
                                <Button variant="outline" onClick={() => handleSort('sortir_2')}><span className="mr-auto">Sort 2</span><Badge>2</Badge></Button>
                                <Button variant="outline" onClick={() => handleSort('sortir_3')}><span className="mr-auto">Sort 3</span><Badge>3</Badge></Button>
                                <Button variant="destructive" onClick={() => handleSort('rejected')}><span className="mr-auto">Reject</span><Badge>X</Badge></Button>
                                <Button variant="secondary" onClick={() => navigate('next')} className="col-span-2"><span className="mr-auto">Skip</span><Badge>S</Badge></Button>
                                <Button variant="ghost" onClick={handleUndo} className="col-span-2"><Undo2 className="mr-2 h-4 w-4"/> Undo <Badge>Z</Badge></Button>
                             </div>
                        </div>

                         <div className="space-y-2 text-sm text-muted-foreground mt-auto">
                            <p><strong className="font-semibold text-foreground">Total Photos:</strong> {photos.length}</p>
                            <p><strong className="font-semibold text-foreground">Sorted:</strong> {photos.length - unsortedPhotos.length}</p>
                            <p><strong className="font-semibold text-foreground">Remaining:</strong> {unsortedPhotos.length}</p>
                        </div>
                    </div>
                </div>
                 ) : (
                    <div className="flex items-center justify-center h-full text-muted-foreground">
                        <p>No photos left to sort.</p>
                    </div>
                )}
            </TabsContent>
            <TabsContent value="ai" className="h-full mt-0 overflow-y-auto p-4">
                 <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                    {photos.map(photo => {
                        const autoFolder = getAutoSortFolder(photo.aiScore);
                        return (
                        <Card key={photo.id} className="overflow-hidden group">
                            <CardContent className="p-0 aspect-square relative">
                                <Image src={photo.dataUri} alt={photo.name} fill className="object-cover"/>
                                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-2 text-white">
                                    <p className="text-xs font-semibold truncate">{photo.name}</p>
                                </div>
                                {photo.isDuplicate && <Badge variant="destructive" className="absolute top-2 right-2">Similar</Badge>}
                            </CardContent>
                            <div className="p-2 text-sm">
                                <p className="font-semibold">Score: {photo.aiScore ?? 'N/A'}</p>
                                <p className="text-xs text-muted-foreground">AI Suggestion: <span className={`font-medium ${autoFolder === 'Best' ? 'text-green-400' : autoFolder === 'Good' ? 'text-blue-400' : 'text-red-400'}`}>{autoFolder}</span></p>
                            </div>
                        </Card>
                        )
                    })}
                </div>
            </TabsContent>
        </main>
      </div>
    </TooltipProvider>
  );
}
