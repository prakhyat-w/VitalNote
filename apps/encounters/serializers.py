from rest_framework import serializers

from .models import Encounter, SOAPNote, Transcript

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
    "audio/ogg",
    "video/mp4",
}


class SOAPNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SOAPNote
        fields = ["subjective", "objective", "assessment", "plan", "created_at"]


class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = ["raw_text", "redacted_text", "created_at"]


class EncounterSerializer(serializers.ModelSerializer):
    soap_note = SOAPNoteSerializer(read_only=True)
    transcript = TranscriptSerializer(read_only=True)

    class Meta:
        model = Encounter
        fields = [
            "id",
            "status",
            "original_filename",
            "error_message",
            "created_at",
            "updated_at",
            "transcript",
            "soap_note",
        ]


class EncounterCreateSerializer(serializers.Serializer):
    audio_file = serializers.FileField()

    def validate_audio_file(self, value):
        if value.content_type not in ALLOWED_AUDIO_TYPES:
            raise serializers.ValidationError(
                "Unsupported file type. Please upload an MP3, WAV, or M4A file."
            )
        max_size = 25 * 1024 * 1024  # 25 MB
        if value.size > max_size:
            raise serializers.ValidationError("File size must be under 25 MB.")
        return value
