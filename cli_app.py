import random
import os
import json
from lxml import etree as ET


# Function to generate a random company name
def generate_company_name():
    adjectives = ["Global", "Dynamic", "Innovative","Creative", "Efficient", "Strategic", "Advanced", "Leading", "NextGen", 
                  "Prime", "Smart", "Agile", "Proactive", "Zeus", "Hercules", "Athena", "Apollo", "Hermes", "Artemis", "Ares", 
                  "Hades", "Poseidon", "Demeter", "Hestia", "Hera", "Persephone", "Dionysus", "Hephaestus", "Aphrodite", "Hermes", 
                  "Athena", "Hera", "Artemis", "Apollo", "Hades", "Poseidon", "Demeter", "Hestia", "Persephone", "Dionysus", "Hephaestus", 
                  "Aphrodite", "Hermes", "Athena", "Hera", "Artemis", "Apollo", "Hades", "Poseidon", "Demeter", "Hestia", "Persephone", 
                  "Dionysus", "Hephaestus", "Aphrodite", "Hermes", "Athena", "Hera", "Artemis", "Apollo", "Hades", "Poseidon", "Demeter", 
                  "Hestia", "Persephone", "Dionysus", "Hephaestus", "Aphrodite", "Hermes", "Athena", "Hera", "Artemis", "Apollo", "Hades", 
                  "Poseidon", "Demeter", "Hestia", "Persephone", "Dionysus", "Hephaestus", "Aphrodite", "Hermes", "Athena", "Hera", 
                  "Artemis", "Apollo", "Hades", "Poseidon", "Demeter", "Hestia", "Persephone", "Dionysus", "Hephaestus", "Aphrodite", 
                  "Hermes", "Athena", "Hera", "Artemis", "Apollo", "Hades", "Poseidon", "Demeter", "Hestia", "Persephone", "Dionys"]
    nouns = ["Solutions", "Technologies", "Systems", "Concepts", "Networks", "Industries", "Enterprises", "Holdings", "Services", "Ventures"]
    return f"{random.choice(adjectives)} {random.choice(nouns)}"


def main():
    # Input the number of invoices to create
    while True:
        user_input = input("How many invoices do you want to create ? (Between 1 et 100): ")
        if user_input.isdigit():
            count = int(user_input)
            if 1 <= count <= 100:
                break
        print("Erreur: veuillez entrer un nombre valide entre 1 et 100.")

    # Date input
    while True:
        invoice_date = input("Entrez la date de la facture (au format yyyymmdd): ")
        if len(invoice_date) == 8 and invoice_date.isdigit():
            break
        print("Format invalide. Réessayez.")

    # opening of the base sample0 file
    tree = ET.parse("setup_file/sample0.xml")
    root = tree.getroot()
    namespaces = {
        'xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'udt': "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
        'rsm': "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        'ram': "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
    }

    # loading of the file lifecycle
    with open("setup_file/lifecycles", encoding="utf-8") as lf:
        lifecycles = json.load(lf)["Lifecycles"]

    for _ in range(count):
        invoice_number = f"INV-{random.randint(1000, 99999999):08d}"
        invoice = ET.ElementTree(ET.fromstring(ET.tostring(root)))

        # Update Invoice number
        invoice.find(".//ram:ID", namespaces=namespaces).text = invoice_number

        # Update Invoice date
        invoice.find(".//udt:DateTimeString", namespaces=namespaces).text = invoice_date

        # Random creation of the lifecycle
        chosen_states = []

        # Forced "Submitted" as first state
        submitted_state = next((s for s in lifecycles if s["State"] == "Submitted"), None)
        if submitted_state:
            s_copy = submitted_state.copy()
            s_copy["DelayInSeconds"] = random.randint(3, 20)
            chosen_states.append(s_copy)

        # add next states respecting the order
        for state in lifecycles:
            if state["State"] == "Submitted":
                continue
            if random.choice([True, False]):
                state_copy = state.copy()
                state_copy["DelayInSeconds"] = random.randint(3, 20)
                if state_copy["State"] in ["Suspended", "PaymentSent"]:
                    if random.choice([True, False]):
                        state_copy["WaitForAction"] = (
                            "Complete" if state_copy["State"] == "Suspended" 
                            else "ConfirmPayment"
                        )
                chosen_states.append(state_copy)

        # Update Lifecycles in the XML
        content_element = invoice.find(".//ram:Content", namespaces=namespaces)
        content_json = json.loads(content_element.text)
        content_json["Lifecycles"] = chosen_states
        content_element.text = json.dumps(content_json)

        # Update BuyerTradeParty name
        buyer_trade_party = invoice.find(".//ram:BuyerTradeParty/ram:Name", namespaces=namespaces)
        if buyer_trade_party is not None:
            buyer_trade_party.text = generate_company_name()

        # Final XML conversion
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", f"{invoice_number}.xml")
        invoice.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

if __name__ == "__main__":
    main()