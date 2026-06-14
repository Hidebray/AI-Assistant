import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';

export const useSpeechRecognition = (onTranscriptChange: (transcript: string) => void) => {
  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);
  const callbackRef = useRef(onTranscriptChange);
  const { i18n } = useTranslation();

  useEffect(() => {
    callbackRef.current = onTranscriptChange;
  }, [onTranscriptChange]);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    
    // Set language based on the current i18n selection
    recognition.lang = i18n.language === 'vi' ? 'vi-VN' : 'en-US';

    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        transcript += event.results[i][0].transcript;
      }
      if (callbackRef.current) {
        callbackRef.current(transcript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [i18n.language]);

  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) {
      console.warn('Speech Recognition is not supported in this browser.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsListening(true);
      } catch (e) {
        console.error('Failed to start speech recognition', e);
      }
    }
  }, [isListening]);

  return {
    isListening,
    toggleListening,
    isSupported: !!((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition)
  };
};
