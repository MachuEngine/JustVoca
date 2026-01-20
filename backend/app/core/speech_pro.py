import requests
import base64
import re
import subprocess
import tempfile
import os
import time

class SpeechProProvider:
    def __init__(self):
        # 명세서에 명시된 Base URL
        self.base_url = "http://112.220.79.222:33005/speechpro"

    def _normalize_text(self, text):
        # 명세서 4번 항목: NBSP(\u00A0) 등 특수 공백 제거 및 정규화
        return re.sub(r'[\u00A0\u2002\u2003\u2009\t\s]+', ' ', text).strip()

    def _convert_to_wav(self, audio_bytes):
        """브라우저의 WebM 데이터를 엔진이 인식 가능한 16k Mono WAV로 변환"""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_in:
            temp_in.write(audio_bytes)
            temp_in_path = temp_in.name
        
        temp_out_path = temp_in_path + ".wav"
        
        try:
            # 명세서 권장 사양: 16000Hz, 1채널(Mono), 16-bit PCM
            command = [
                "ffmpeg", "-y", "-i", temp_in_path,
                "-ar", "16000", "-ac", "1", "-acodec", "pcm_s16le", temp_out_path
            ]
            # stderr=subprocess.PIPE를 통해 FFmpeg 에러 메시지 캡처 가능
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            with open(temp_out_path, "rb") as f:
                data = f.read()
                print(f"--- [진단] 변환된 WAV 크기: {len(data)} bytes ---")
                return data
        finally:
            if os.path.exists(temp_in_path): os.remove(temp_in_path)
            if os.path.exists(temp_out_path): os.remove(temp_out_path)

    def get_evaluation(self, text: str, audio_bytes: bytes):
        try:
            # 0단계: 오디오 변환 (16k Mono WAV)
            converted_wav = self._convert_to_wav(audio_bytes)
            if not converted_wav or len(converted_wav) < 1000:
                return {"error": "AUDIO_EMPTY", "message": "녹음 데이터가 없거나 너무 작습니다."}

            normalized_text = self._normalize_text(text)
            request_id = f"test_{int(time.time())}"

            # 1단계: GTP 호출 (음소 변환)
            gtp_res = requests.post(f"{self.base_url}/gtp", 
                                    json={"id": request_id, "text": normalized_text}, timeout=15).json()
            
            # 에러 코드 확인 (명세서의 0번 확인)
            if gtp_res.get("error code", gtp_res.get("error_code", 0)) != 0: 
                return {"error": "GTP_FAILED", "detail": gtp_res}

            # [필독] 엔진 응답에서 데이터를 공백/언더바 구분 없이 가져옵니다.
            syll_ltrs = gtp_res.get("syll ltrs") or gtp_res.get("syll_ltrs")
            syll_phns = gtp_res.get("syll phns") or gtp_res.get("syll_phns")

            # 2단계: Model 호출 (발음 평가용 FST 모델 생성)
            model_req = {
                "id": request_id, 
                "text": normalized_text,
                "syll ltrs": syll_ltrs, # 명세서 기준
                "syll phns": syll_phns
            }
            model_res = requests.post(f"{self.base_url}/model", json=model_req, timeout=15).json()
            
            if model_res.get("error code", model_res.get("error_code", 0)) != 0: 
                return {"error": "MODEL_FAILED", "detail": model_res}

            # 3단계: Score 호출 (최종 채점)
            wav_base64 = base64.b64encode(converted_wav).decode('utf-8')
            
            # [핵심 수정] 명세서 규격과 참고 코드의 규격을 최대한 절충하여 구성합니다.
            score_req = {
                "id": request_id, 
                "text": normalized_text,
                "syll ltrs": model_res.get("syll ltrs") or model_res.get("syll_ltrs"),
                "syll phns": model_res.get("syll phns") or model_res.get("syll_phns"),
                "fst": model_res.get("fst"),
                "wav usr": wav_base64 # 명세서의 wav usr 필드
            }

            # 로그 확인용 (디버그 시 활성화)
            # print(f"--- [DEBUG] Score 요청 필드 확인: {list(score_req.keys())} ---")

            try:
                # 연산 시간이 길어질 수 있으므로 timeout을 45초로 넉넉히 잡습니다.
                response = requests.post(f"{self.base_url}/scorejson", json=score_req, timeout=45)
                
                # 서버가 데이터를 보내다 죽었는지(15바이트 에러) 확인
                if not response.text:
                    return {"error": "EMPTY_RESPONSE", "message": "엔진 서버가 응답 도중 연결을 끊었습니다."}
                    
                return response.json()
                
            except requests.exceptions.ChunkedEncodingError:
                # 이 에러가 발생하면 서버 메모리나 설정 문제일 확률이 높습니다.
                return {"error": "INCOMPLETE_READ", "message": "서버가 채점 도중 강제 종료되었습니다."}

        except Exception as e:
            return {"error": "SYSTEM_ERROR", "message": str(e)}

# 클래스 인스턴스 생성
speech_provider = SpeechProProvider()