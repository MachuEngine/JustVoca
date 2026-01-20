import requests
import base64
import re
import time
import json

class SpeechProProvider:
    def __init__(self):
        # 실제 엔진 URL
        self.base_url = "http://112.220.79.222:33005/speechpro"

    def _normalize_text(self, text: str):
        return re.sub(r'[\u00A0\u2002\u2003\u2009\t\s]+', ' ', text).strip()

    def get_evaluation(self, text: str, audio_bytes: bytes):
        normalized_text = self._normalize_text(text)
        request_id = f"voca_{int(time.time())}"

        try:
            # 1. GTP
            gtp_res = requests.post(
                f"{self.base_url}/gtp", 
                json={"id": request_id, "text": normalized_text},
                timeout=10
            ).json()

            if "syll ltrs" not in gtp_res:
                return {"success": False, "error": "GTP 단계 실패", "detail": gtp_res}

            # 2. Model
            model_res = requests.post(f"{self.base_url}/model", json={
                "id": request_id, 
                "text": normalized_text,
                "syll ltrs": gtp_res["syll ltrs"], 
                "syll phns": gtp_res["syll phns"]
            }, timeout=10).json()

            if "fst" not in model_res:
                return {"success": False, "error": "Model 생성 실패", "detail": model_res}

            # 3. Score
            wav_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # [수정] syll ltrs/phns는 GTP 결과(gtp_res) 사용
            score_res = requests.post(f"{self.base_url}/scorejson", json={
                "id": request_id, 
                "text": normalized_text,
                "syll ltrs": gtp_res["syll ltrs"],  
                "syll phns": gtp_res["syll phns"],  
                "fst": model_res["fst"], 
                "wav usr": wav_base64
            }, timeout=30).json()

            # [확인] 별도 가공 없이 엔진 응답 원본을 그대로 반환 (symbol 필드가 이미 포함됨)
            return {"success": True, "data": score_res}

        except Exception as e:
            print(f"[ERROR] 연동 중 예외 발생: {str(e)}")
            return {"success": False, "error": f"연동 중 예외 발생: {str(e)}"}

speech_provider = SpeechProProvider()