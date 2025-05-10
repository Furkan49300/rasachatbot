import firebase_admin
from firebase_admin import credentials, firestore
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

class ActionSaveReservation(Action):
    def name(self):
        return "action_save_reservation"

    def run(self, dispatcher, tracker, domain):
        date = tracker.get_slot("date")
        number = tracker.get_slot("number")
        name = tracker.get_slot("name")
        phone = tracker.get_slot("phone")

        reservation_data = {
            "date": date,
            "number_of_people": number,
            "name": name,
            "phone": phone
        }

        doc_ref = db.collection("reservations").add(reservation_data)
        reservation_id = doc_ref[1].id  

        dispatcher.utter_message(f" Votre réservation a été enregistrée avec succès.\n Numéro de réservation : **{reservation_id}**")

        return []


class ActionGetReservationNumber(Action):
    def name(self):
        return "action_get_reservation_number"

    def run(self, dispatcher, tracker, domain):
        name = tracker.get_slot("name")
        phone = tracker.get_slot("phone")

        results = db.collection("reservations")\
            .where("name", "==", name)\
            .where("phone", "==", phone)\
            .stream()

        for doc in results:
            dispatcher.utter_message(f"Votre numéro de réservation est : {doc.id}")
            return []

        dispatcher.utter_message("Aucune réservation trouvée avec ces informations.")
        return []

class ActionAddComment(Action):
    def name(self):
        return "action_add_comment"

    def run(self, dispatcher, tracker, domain):
        name = tracker.get_slot("name")
        phone = tracker.get_slot("phone")
        comment = tracker.get_slot("comment")

        results = db.collection("reservations")\
            .where("name", "==", name)\
            .where("phone", "==", phone)\
            .stream()

        for doc in results:
            db.collection("reservations").document(doc.id).update({
                "comment": comment
            })
            dispatcher.utter_message("Votre commentaire a été ajouté.")
            return []

        dispatcher.utter_message("Impossible d’ajouter le commentaire. Aucune réservation trouvée.")
        return []
        
class ActionShowReservationById(Action):
    def name(self):
        return "action_show_reservation_by_id"

    def run(self, dispatcher, tracker, domain):
        reservation_id = tracker.get_slot("reservation_id")

        if not reservation_id:
            dispatcher.utter_message("Quel est votre numéro de réservation ?")
            return []

        try:
            doc = db.collection("reservations").document(reservation_id).get()

            if doc.exists:
                data = doc.to_dict()
                name = data.get("name", "inconnu")
                date = data.get("date", "non précisée")
                number = data.get("number_of_people", "non précisé")
                comment = data.get("comment", "aucun")
                phone=data.get("phone","aucun")

                dispatcher.utter_message(
                    f" **Réservation** `{reservation_id}` :\n"
                    f"-  Nom : {name}\n"
                    f"-  Date : {date}\n"
                    f"-  Nombre de personnes : {number}\n"
                    f"-  Commentaire : {comment}\n"
                    f"-  Téléphone : {phone}"
                )
            else:
                dispatcher.utter_message("Aucune réservation trouvée avec ce numéro.")

        except Exception as e:
            dispatcher.utter_message("Une erreur est survenue.")
            print(f"Erreur Firestore : {e}")

        return []

class ActionCancelReservation(Action):
    def name(self):
        return "action_cancel_reservation"

    def run(self, dispatcher, tracker, domain):
        reservation_id = tracker.get_slot("reservation_id")

        if not reservation_id:
            dispatcher.utter_message("Quel est votre numéro de réservation à annuler ?")
            return []

        try:
            doc_ref = db.collection("reservations").document(reservation_id)
            doc = doc_ref.get()

            if doc.exists:
                doc_ref.delete()
                dispatcher.utter_message(f"Votre réservation `{reservation_id}` a bien été annulée.")
            else:
                dispatcher.utter_message( "Aucune réservation trouvée avec ce numéro.")

        except Exception as e:
            dispatcher.utter_message(" Une erreur est survenue.")
            print(f"Erreur Firestore (annulation) : {e}")

        return []
