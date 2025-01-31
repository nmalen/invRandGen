import random
import os
import json
from lxml import etree as ET


# Function to generate a random company name
def generate_company_name(adjectives, nouns):
    return f"{random.choice(adjectives)} {random.choice(nouns)}"


# Function to generate a random 9-digit number
def generate_random_tax_id():
    return f"FR{random.randint(100000000, 999999999)}"


# Function to generate a random person name
def generate_person_name(first_names, last_names):
    return f"{random.choice(first_names)}. {random.choice(last_names)}"


# Function to generate a random postal address
def generate_postal_address(street_types, street_names, city_names, country_id):
    random_zip = f"{random.randint(10000, 97999)}"
    street_number = random.randint(1, 100)
    line_one = f"{street_number} {random.choice(street_types)} {random.choice(street_names)}"
    city_name = random.choice(city_names)
    return random_zip, line_one, city_name, country_id


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

    # Remove existing IncludedSupplyChainTradeLineItem elements
    for elem in root.findall(".//ram:IncludedSupplyChainTradeLineItem", namespaces=namespaces):
        elem.getparent().remove(elem)

    # loading of the file lifecycle
    with open("setup_file/lifecycles", encoding="utf-8") as lf:
        lifecycles = json.load(lf)["Lifecycles"]

    # loading of the buyers setup file
    with open("setup_file/buyers_setup.json", encoding="utf-8") as bf:
        buyers_setup = json.load(bf)
        adjectives = buyers_setup["adjectives"]
        nouns = buyers_setup["nouns"]
        first_names = buyers_setup["first_names"]
        last_names = buyers_setup["last_names"]
        street_types = buyers_setup["street_type"]
        street_names = buyers_setup["street_name"]
        city_names = buyers_setup["city_name"]
        country_id = buyers_setup["country_id"]

    # loading of the seller setup file
    with open("setup_file/seller_setup.json", encoding="utf-8") as sf:
        seller_setup = json.load(sf)

    # loading of the items setup file
    with open("setup_file/items_setup.json", encoding="utf-8") as isf:
        items_setup = json.load(isf)
        items = items_setup["items"]
        max_number_of_items = items_setup["max_number_of_items"]

    for _ in range(count):
        invoice_number = f"INV-{random.randint(1000, 99999999):08d}"
        invoice = ET.ElementTree(ET.fromstring(ET.tostring(root)))

        # Ensure ram:ID in GuidelineSpecifiedDocumentContextParameter contains urn:cen.eu:en16931:2017
        guideline_id = invoice.find(".//ram:GuidelineSpecifiedDocumentContextParameter/ram:ID", namespaces=namespaces)
        guideline_id.text = "urn:cen.eu:en16931:2017"

        # Update Invoice number
        invoice_id = invoice.find(".//rsm:ExchangedDocument/ram:ID", namespaces=namespaces)
        invoice_id.text = invoice_number

        # Update Invoice date
        invoice.find(".//udt:DateTimeString", namespaces=namespaces).text = invoice_date

        # Random creation of the lifecycle
        chosen_states = []

        # Forced "Submitted" as first state
        submitted_state = next((s for s in lifecycles if s["State"] == "Submitted"), None)
        if submitted_state:
            s_copy = submitted_state.copy()
            s_copy["DelayInSeconds"] = random.randint(1, 10)
            chosen_states.append(s_copy)

        # add next states respecting the order
        for state in lifecycles:
            if state["State"] == "Submitted":
                continue
            if random.choice([True, False]):
                state_copy = state.copy()
                state_copy["DelayInSeconds"] = random.randint(1, 10)
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
            buyer_trade_party.text = generate_company_name(adjectives, nouns)

        # Generate and update BuyerTradeParty tax ID
        buyer_tax_id = generate_random_tax_id()
        buyer_trade_party_id = invoice.find(".//ram:BuyerTradeParty/ram:ID", namespaces=namespaces)
        if buyer_trade_party_id is not None:
            buyer_trade_party_id.text = buyer_tax_id
        tax_registration = invoice.find(".//ram:BuyerTradeParty/ram:SpecifiedTaxRegistration/ram:ID", namespaces=namespaces)
        if tax_registration is not None:
            tax_registration.text = buyer_tax_id
        legal_organization_id = invoice.find(".//ram:BuyerTradeParty/ram:SpecifiedLegalOrganization/ram:ID", namespaces=namespaces)
        if legal_organization_id is not None:
            legal_organization_id.text = buyer_tax_id

        # Update BuyerTradeParty contact person name
        trade_contact = invoice.find(".//ram:BuyerTradeParty/ram:DefinedTradeContact/ram:PersonName", namespaces=namespaces)
        if trade_contact is not None:
            trade_contact.text = generate_person_name(first_names, last_names)

        # Generate and update BuyerTradeParty postal address
        random_zip, line_one, city_name, country_id = generate_postal_address(street_types, street_names, city_names, country_id)
        postal_address = invoice.find(".//ram:BuyerTradeParty/ram:PostalTradeAddress", namespaces=namespaces)
        if postal_address is not None:
            postal_address.find("ram:PostcodeCode", namespaces=namespaces).text = random_zip
            postal_address.find("ram:LineOne", namespaces=namespaces).text = line_one
            postal_address.find("ram:CityName", namespaces=namespaces).text = city_name
            postal_address.find("ram:CountryID", namespaces=namespaces).text = country_id

        # Generate and update IncludedSupplyChainTradeLineItem
        items_number = random.randint(1, 10)
        supply_chain_trade_transaction = invoice.find(".//rsm:SupplyChainTradeTransaction", namespaces=namespaces)
        for i in range(1, items_number + 1):
            item = random.choice(items)
            billed_quantity = random.randint(1, max_number_of_items)
            line_total_amount = item["price"] * billed_quantity

            trade_line_item = ET.SubElement(supply_chain_trade_transaction, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}IncludedSupplyChainTradeLineItem")
            associated_document = ET.SubElement(trade_line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}AssociatedDocumentLineDocument")
            ET.SubElement(associated_document, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}LineID").text = str(i)
            specified_trade_product = ET.SubElement(trade_line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedTradeProduct")
            ET.SubElement(specified_trade_product, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SellerAssignedID").text = item["reference"]
            ET.SubElement(specified_trade_product, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}Name").text = item["name"]
            specified_line_trade_agreement = ET.SubElement(trade_line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedLineTradeAgreement")
            net_price_product_trade_price = ET.SubElement(specified_line_trade_agreement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}NetPriceProductTradePrice")
            ET.SubElement(net_price_product_trade_price, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ChargeAmount").text = str(item["price"])
            specified_line_trade_delivery = ET.SubElement(trade_line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedLineTradeDelivery")
            ET.SubElement(specified_line_trade_delivery, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}BilledQuantity", unitCode="H87").text = str(billed_quantity)
            specified_line_trade_settlement = ET.SubElement(trade_line_item, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedLineTradeSettlement")
            applicable_trade_tax = ET.SubElement(specified_line_trade_settlement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}ApplicableTradeTax")
            ET.SubElement(applicable_trade_tax, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}TypeCode").text = "VAT"
            ET.SubElement(applicable_trade_tax, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}CategoryCode").text = "S"
            ET.SubElement(applicable_trade_tax, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}RateApplicablePercent").text = str(item["vat_rate"])
            specified_trade_settlement_line_monetary_summation = ET.SubElement(specified_line_trade_settlement, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}SpecifiedTradeSettlementLineMonetarySummation")
            ET.SubElement(specified_trade_settlement_line_monetary_summation, "{urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100}LineTotalAmount").text = str(line_total_amount)

        # Add ApplicableHeaderTradeAgreement before ApplicableHeaderTradeDelivery
        applicable_header_trade_agreement = invoice.find(".//ram:ApplicableHeaderTradeAgreement", namespaces=namespaces)
        applicable_header_trade_delivery = invoice.find(".//ram:ApplicableHeaderTradeDelivery", namespaces=namespaces)
        if applicable_header_trade_agreement is not None and applicable_header_trade_delivery is not None:
            supply_chain_trade_transaction.insert(supply_chain_trade_transaction.index(applicable_header_trade_delivery), applicable_header_trade_agreement)

        # Update SellerTradeParty information
        seller_trade_party = invoice.find(".//ram:SellerTradeParty", namespaces=namespaces)
        if seller_trade_party is not None:
            seller_trade_party.find("ram:Name", namespaces=namespaces).text = seller_setup["name"]
            seller_trade_party.find("ram:SpecifiedLegalOrganization/ram:ID", namespaces=namespaces).text = seller_setup["legal_organization_id"]
            postal_address = seller_trade_party.find("ram:PostalTradeAddress", namespaces=namespaces)
            postal_address.find("ram:PostcodeCode", namespaces=namespaces).text = seller_setup["postal_address"]["postcode"]
            postal_address.find("ram:LineOne", namespaces=namespaces).text = seller_setup["postal_address"]["line_one"]
            postal_address.find("ram:CityName", namespaces=namespaces).text = seller_setup["postal_address"]["city"]
            postal_address.find("ram:CountryID", namespaces=namespaces).text = seller_setup["postal_address"]["country_id"]
            tax_registration = seller_trade_party.find("ram:SpecifiedTaxRegistration/ram:ID", namespaces=namespaces)
            tax_registration.set("schemeID", seller_setup["tax_registration_id"]["scheme_id"])
            tax_registration.text = seller_setup["tax_registration_id"]["id"]

        # Update BuyerTradeParty information
        buyer_trade_party = invoice.find(".//ram:BuyerTradeParty", namespaces=namespaces)
        if buyer_trade_party is not None:
            buyer_trade_party.find("ram:Name", namespaces=namespaces).text = generate_company_name(adjectives, nouns)
            buyer_trade_party.find("ram:SpecifiedLegalOrganization/ram:ID", namespaces=namespaces).text = generate_random_tax_id()
            postal_address = buyer_trade_party.find("ram:PostalTradeAddress", namespaces=namespaces)
            random_zip, line_one, city_name, country_id = generate_postal_address(street_types, street_names, city_names, country_id)
            postal_address.find("ram:PostcodeCode", namespaces=namespaces).text = random_zip
            postal_address.find("ram:LineOne", namespaces=namespaces).text = line_one
            postal_address.find("ram:CityName", namespaces=namespaces).text = city_name
            postal_address.find("ram:CountryID", namespaces=namespaces).text = country_id
            tax_registration = buyer_trade_party.find("ram:SpecifiedTaxRegistration/ram:ID", namespaces=namespaces)
            tax_registration.set("schemeID", "VA")
            tax_registration.text = generate_random_tax_id()

        # Reorder root children to match sample0 structure
        rci_root = invoice.getroot()
        exchanged_document_context = rci_root.find("rsm:ExchangedDocumentContext", namespaces=namespaces)
        exchanged_document = rci_root.find("rsm:ExchangedDocument", namespaces=namespaces)
        supply_chain_trade_transaction = rci_root.find("rsm:SupplyChainTradeTransaction", namespaces=namespaces)

        if exchanged_document_context is not None:
            rci_root.remove(exchanged_document_context)
        if exchanged_document is not None:
            rci_root.remove(exchanged_document)
        if supply_chain_trade_transaction is not None:
            rci_root.remove(supply_chain_trade_transaction)

        if exchanged_document_context is not None:
            rci_root.append(exchanged_document_context)
        if exchanged_document is not None:
            rci_root.append(exchanged_document)
        if supply_chain_trade_transaction is not None:
            rci_root.append(supply_chain_trade_transaction)

        # Reorder sub-elements under SupplyChainTradeTransaction
        if supply_chain_trade_transaction is not None:
            applicable_header_trade_agreement = supply_chain_trade_transaction.find("ram:ApplicableHeaderTradeAgreement", namespaces=namespaces)
            applicable_header_trade_delivery = supply_chain_trade_transaction.find("ram:ApplicableHeaderTradeDelivery", namespaces=namespaces)
            applicable_header_trade_settlement = supply_chain_trade_transaction.find("ram:ApplicableHeaderTradeSettlement", namespaces=namespaces)

            for elem in [applicable_header_trade_agreement, applicable_header_trade_delivery, applicable_header_trade_settlement]:
                if elem is not None:
                    supply_chain_trade_transaction.remove(elem)

            for elem in [applicable_header_trade_agreement, applicable_header_trade_delivery, applicable_header_trade_settlement]:
                if elem is not None:
                    supply_chain_trade_transaction.append(elem)

        # Final XML conversion
        os.makedirs("output", exist_ok=True)
        output_path = os.path.join("output", f"{invoice_number}.xml")
        invoice.write(output_path, encoding="utf-8", xml_declaration=True, pretty_print=True)

        # Add newlines after closing tags for readability
        with open(output_path, 'r', encoding='utf-8') as file:
            content = file.read()

        content = content.replace("<?xml version='1.0' encoding='UTF-8'?>",
                                  "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<!--\n\n    Licensed under European Union Public Licence (EUPL) version 1.2.\n\n-->\n<!-- XML instance generated by Andreas Pelekies -->\n<!-- Example 1: Invoice with multiple line items for EN16931 -->\n<!-- Timestamp: 2017-08-24 00:00:00 +0200 -->\n")

        content = content.replace('</ram:ApplicableHeaderTradeSettlement>', '</ram:ApplicableHeaderTradeSettlement>\n')
        content = content.replace('</ram:IncludedSupplyChainTradeLineItem>', '</ram:IncludedSupplyChainTradeLineItem>\n')

        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)

if __name__ == "__main__":
    main()