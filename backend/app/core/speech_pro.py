import requests
import base64
import re
import time
import json

class SpeechProProvider:
    def __init__(self):
        self.base_url = "http://112.220.79.222:33005/speechpro"

    def _normalize_text(self, text: str):
        return re.sub(r'[\u00A0\u2002\u2003\u2009\t\s]+', ' ', text).strip()

    def get_evaluation(self, text: str, audio_bytes: bytes):
        normalized_text = self._normalize_text(text)
        request_id = f"voca_{int(time.time())}"

        try:
            # --- 1단계: GTP 호출 ---
            print(f"\n[DEBUG] GTP 요청 시작 - ID: {request_id}, Text: {normalized_text}")
            gtp_response = requests.post(
                f"{self.base_url}/gtp", 
                json={"id": request_id, "text": normalized_text},
                timeout=10
            )
            gtp_res = gtp_response.json()
            print(f"[DEBUG] GTP 응답 내용: {json.dumps(gtp_res, ensure_ascii=False)}")

            if "syll ltrs" not in gtp_res:
                return {"success": False, "error": "GTP 단계 실패", "detail": gtp_res}

            # --- 2단계: Model 호출 ---
            print(f"[DEBUG] Model 요청 시작")
            model_response = requests.post(f"{self.base_url}/model", json={
                "id": request_id, 
                "text": normalized_text,
                "syll ltrs": gtp_res["syll ltrs"], 
                "syll phns": gtp_res["syll phns"]
            }, timeout=10)
            
            model_res = model_response.json()
            print(f"[DEBUG] Model 응답 내용: {json.dumps(model_res, ensure_ascii=False)}")

            if "fst" not in model_res:
                return {"success": False, "error": "Model 생성 실패", "detail": model_res}

            # --- 3단계: Score 호출 ---
            print(f"[DEBUG] Score 요청 시작 (오디오 데이터 전송)")
            wav_base64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            # [수정 포인트] syll ltrs와 syll phns를 model_res가 아닌 gtp_res에서 가져옴
            score_response = requests.post(f"{self.base_url}/scorejson", json={
                "id": request_id, 
                "text": normalized_text,
                "syll ltrs": gtp_res["syll ltrs"],  
                "syll phns": gtp_res["syll phns"],  
                "fst": model_res["fst"], 
                "wav usr": wav_base64
            }, timeout=30)
            
            score_res = score_response.json()
            print(f"[DEBUG] 최종 Score 응답: {json.dumps(score_res, ensure_ascii=False)}")

            return {"success": True, "data": score_res}

        except Exception as e:
            print(f"[ERROR] 연동 중 예외 발생: {str(e)}")
            return {"success": False, "error": f"연동 중 예외 발생: {str(e)}"}

speech_provider = SpeechProProvider()