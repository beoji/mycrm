from django.core.exceptions import ValidationError


def validate_wartosc_umowa(value):
	error_message = "Wprowadź poprawną wartość umowy"
	if value < 10:
		raise ValidationError(
			error_message
		)

def validate_nip(value):
	error_message = "Wprowadź poprawny numer NIP"
	try:
		val = int(value)
	except ValueError:
		raise ValidationError(
			error_message
		)
	if len(value) != 10:
		raise ValidationError(
			error_message
		)
