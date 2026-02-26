from src.extract_exhibitors import parse_exhibitor_block


def test_parse_exhibitor_block_extracts_core_fields() -> None:
    block = """20 MICRONS LIMITED
Plot No : 9/10, G.I.D.C., Estate, Waghodia, Vadodara - 391760, Gujarat, India
Tel : 91 2668 264082 Mobile : 91 9099913617
Email : mishra@20microns.com
Contact :Krishna Kumar Mishra, President - Product & Business Development
Company Profile :20 Microns Limited, India's largest industrial minerals manufacturer."""

    record = parse_exhibitor_block(block, serial_no=1)

    assert record.company_name == "MICRONS LIMITED"
    assert "Waghodia" in record.address
    assert record.tel == "91 2668 264082"
    assert record.mobile == "91 9099913617"
    assert record.email == "mishra@20microns.com"
    assert record.contact_person_name == "Krishna Kumar Mishra"
    assert "President" in record.contact_person_designation
    assert "20 Microns Limited" in record.company_profile


def test_parse_exhibitor_block_without_contact_designation() -> None:
    block = """99 BUSINESS MEDIA
1201, 12th Floor, Gopal Heights, Netaji Subhash Place, Pitampura, Delhi
Email : ntw2020@gmail.com
Contact : Dr Raj Joshi
Company Profile : 99 Plastic & Packaging journal."""

    record = parse_exhibitor_block(block, serial_no=2)

    assert record.company_name == "BUSINESS MEDIA"
    assert record.contact_person_name == "Dr Raj Joshi"
    assert record.contact_person_designation == ""
