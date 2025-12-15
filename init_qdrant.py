"""
Initialize Qdrant Collections and Add Sample FAQs
"""

import asyncio
from app.services.qdrant_service import qdrant_service
from app.core.config import settings

# Sample FAQs - Indonesian
sample_faqs_id = [
    {
        "question": "Berapa biaya kuliah di Kampus Gratis Indonesia?",
        "answer": "Kuliah di Kampus Gratis Indonesia sepenuhnya GRATIS. Tidak ada biaya pendaftaran, SPP, praktikum, atau biaya tersembunyi apapun. Semua biaya pendidikan ditanggung penuh oleh donatur dan mitra yang peduli pendidikan.",
        "category": "biaya"
    },
    {
        "question": "Apa saja jurusan yang tersedia?",
        "answer": "Kampus Gratis Indonesia menyediakan 5 jurusan unggulan: (1) Teknik Informatika, (2) Sistem Informasi, (3) Manajemen Bisnis, (4) Akuntansi, dan (5) Desain Grafis. Semua jurusan terakreditasi dan diajar oleh dosen berpengalaman.",
        "category": "akademik"
    },
    {
        "question": "Bagaimana cara mendaftar?",
        "answer": "Pendaftaran dilakukan online melalui website. Cukup isi formulir pendaftaran, upload dokumen yang diperlukan (KTP, Ijazah/SKL, Foto), dan tunggu verifikasi dalam 1-3 hari kerja. Tidak ada biaya pendaftaran.",
        "category": "pendaftaran"
    },
    {
        "question": "Dimana lokasi kampus?",
        "answer": "Kampus Gratis Indonesia berlokasi di Jl. Pendidikan No. 123, Jakarta Selatan. Mudah diakses dengan transportasi umum (dekat stasiun dan halte busway).",
        "category": "lokasi"
    },
    {
        "question": "Berapa lama masa studi?",
        "answer": "Masa studi untuk program S1 adalah 4 tahun (8 semester). Namun, mahasiswa dapat menyelesaikan lebih cepat dengan mengambil SKS maksimal atau lebih lama hingga maksimal 7 tahun.",
        "category": "akademik"
    }
]

# Sample FAQs - English
sample_faqs_en = [
    {
        "question": "What is the tuition fee at Kampus Gratis Indonesia?",
        "answer": "Study at Kampus Gratis Indonesia is completely FREE. There are no registration fees, tuition fees, lab fees, or hidden costs. All educational expenses are fully covered by donors and education-focused partners.",
        "category": "fees"
    },
    {
        "question": "What programs are available?",
        "answer": "Kampus Gratis Indonesia offers 5 excellent programs: (1) Computer Science, (2) Information Systems, (3) Business Management, (4) Accounting, and (5) Graphic Design. All programs are accredited and taught by experienced faculty.",
        "category": "academic"
    },
    {
        "question": "How do I apply?",
        "answer": "Registration is done online through our website. Simply fill out the registration form, upload required documents (ID card, diploma/certificate, photo), and wait for verification within 1-3 business days. There is no registration fee.",
        "category": "admission"
    },
    {
        "question": "Where is the campus located?",
        "answer": "Kampus Gratis Indonesia is located at Jl. Pendidikan No. 123, South Jakarta. It is easily accessible by public transportation (near train station and bus stops).",
        "category": "location"
    },
    {
        "question": "How long is the study period?",
        "answer": "The study period for undergraduate programs is 4 years (8 semesters). However, students can finish earlier by taking maximum credits or extend up to a maximum of 7 years.",
        "category": "academic"
    }
]

async def initialize():
    print("=" * 70)
    print("Initializing Qdrant Collections and Sample FAQs")
    print("=" * 70)
    
    # 1. Initialize collections
    print("\n1. Creating collections...")
    qdrant_service.initialize_collections()
    
    # 2. Add Indonesian FAQs
    print("\n2. Adding Indonesian FAQs...")
    ids_id = qdrant_service.add_faqs_batch(
        collection_name=settings.QDRANT_COLLECTION_FAQ_ID,
        faqs=sample_faqs_id
    )
    print(f"   ✅ Added {len(ids_id)} Indonesian FAQs")
    
    # 3. Add English FAQs
    print("\n3. Adding English FAQs...")
    ids_en = qdrant_service.add_faqs_batch(
        collection_name=settings.QDRANT_COLLECTION_FAQ_EN,
        faqs=sample_faqs_en
    )
    print(f"   ✅ Added {len(ids_en)} English FAQs")
    
    # 4. Verify collections
    print("\n4. Verifying collections...")
    info_id = qdrant_service.get_collection_info(settings.QDRANT_COLLECTION_FAQ_ID)
    info_en = qdrant_service.get_collection_info(settings.QDRANT_COLLECTION_FAQ_EN)
    
    print(f"   {settings.QDRANT_COLLECTION_FAQ_ID}:")
    print(f"      Points: {info_id.get('points_count', 0)}")
    print(f"      Status: {info_id.get('status', 'unknown')}")
    
    print(f"   {settings.QDRANT_COLLECTION_FAQ_EN}:")
    print(f"      Points: {info_en.get('points_count', 0)}")
    print(f"      Status: {info_en.get('status', 'unknown')}")
    
    print("\n" + "=" * 70)
    print("✅ Qdrant initialization complete!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(initialize())
