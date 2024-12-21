from .models import Meeting
from .utils import transcribe_audio, upload_to_s3
import requests

def get_gmeet_recordings(meeting_id, access_token):
    url = f"https://www.googleapis.com/calendar/v3/calendars/{meeting_id}/events"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("recordings", [])
    return {"error": response.json()}

def gmeet_recording_to_text_and_upload(meeting_id, access_token):
    recordings = get_gmeet_recordings(meeting_id, access_token)
    if "error" in recordings:
        return recordings

    results = []
    for recording in recordings:
        try:
            audio_url = recording["downloadUrl"]
            job_name = f"gmeet-transcription-{recording['id']}"
            transcription = transcribe_audio(audio_url, job_name)

            s3_key = f"recordings/gmeet/{recording['id']}.mp4"
            s3_url = upload_to_s3(audio_url, s3_key)

            meeting, _ = Meeting.objects.get_or_create(
                meeting_id=meeting_id,
                defaults={
                    "transcription_text": transcription,
                    "recording_url": s3_url,
                    "s3_key": s3_key,
                }
            )
            results.append({
                "recording_id": recording["id"],
                "transcription": transcription,
                "s3_url": s3_url,
            })
        except Exception as e:
            results.append({"recording_id": recording["id"], "error": str(e)})

    return {"meeting_id": meeting_id, "results": results}