package org.kivy.speech;

import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.SpeechRecognizer;
import java.util.ArrayList;

public class KivyRecognitionListener implements RecognitionListener {

    private CallbackWrapper cb;
    public KivyRecognitionListener(CallbackWrapper cb) { this.cb = cb; }

    /* Unused, but must exist */ public void onReadyForSpeech(Bundle b){} public void onBeginningOfSpeech(){}
    public void onRmsChanged(float v){} public void onBufferReceived(byte[] b){}
    public void onEndOfSpeech(){} public void onEvent(int i, Bundle b){}
    public void onError(int e){ cb.callback_data("error", String.valueOf(e)); }

    public void onResults(Bundle bundle){
        ArrayList<String> res = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        cb.callback_data("final", res.get(0));
    }
    public void onPartialResults(Bundle bundle){
        ArrayList<String> res = bundle.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
        cb.callback_data("partial", res.get(0));
    }
} 