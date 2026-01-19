import requests
import base64
import re
import os

class SpeechProProvider:
    def __init__(self):
        self.base_url = "http://112.220.79.222:33005/speechpro"

    def _normalize_text(self, text):
        # 명세서 4번 항목: 특수 공백 제거 로직
        return re.sub(r'[\u00A0\u2002\u2003\u2009\t\s]+', ' ', text).strip()

    def get_evaluation(self, text: str, audio_bytes: bytes):
        normalized_text = self._normalize_text(text)
        request_id = f"voca_{normalized_text[:10]}" # 요청 식별용

        try:
            # 1단계: GTP 호출
            gtp_res = requests.post(f"{self.base_url}/gtp", 
                                    json={"id": request_id, "text": normalized_text}).json()
            if gtp_res.get("error code") != 0: return {"error": "GTP_FAILED"}

            # 2단계: Model 호출
            model_res = requests.post(f"{self.base_url}/model", json={
                "id": request_id, "text": normalized_text,
                "syll ltrs": gtp_res["syll ltrs"], "syll phns": gtp_res["syll phns"]
            }).json()
            if model_res.get("error code") != 0: return {"error": "MODEL_FAILED"}

            # 3단계: Score 호출 (오디오 Base64 변환)
            wav_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            score_res = requests.post(f"{self.base_url}/scorejson", json={
                "id": request_id, "text": normalized_text,
                "syll ltrs": model_res["syll ltrs"], "syll phns": model_res["syll phns"],
                "fst": model_res["fst"], "wav usr": wav_base64
            }).json()

            return score_res
        except Exception as e:
            return {"error": str(e)}