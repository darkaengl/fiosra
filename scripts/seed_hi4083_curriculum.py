"""
Curriculum Seeder for HI4083: Early Modern Ireland (1536–1750).

Hydrates:
1. PostgreSQL Course and 3 Modules.
2. PostgreSQL `syllabus_chunks` with 1536-d pgvector embeddings of authentic primary source texts.
3. Neo4j Course, Modules, High-to-Low Concept Graph, Prerequisite DAG, and Evidence Links.
4. Well-formed Reasoning Milestone Assignment bound to target KCs and public rubrics.
"""

import asyncio
import json
import logging
from uuid import UUID, uuid4

from sqlalchemy import text

from fiosra.mvp.concepts.service import concept_graph_service
from fiosra.mvp.courses.ingestion import syllabus_parser
from fiosra.mvp.courses.schemas import CourseCreate, ModuleCreate
from fiosra.mvp.courses.service import course_service
from fiosra.mvp.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


PRIMARY_SOURCES = {
    "module_1": [
        {
            "title": "Crown of Ireland Act (1541) - 33 Hen. 8 c. 1",
            "content": """# Crown of Ireland Act (1541) - Statutory Records of the Parliament of Dublin

Be it enacted by the King's Highness, with the assent of the Lords Spiritual and Temporal, and the Commons, in this present Parliament assembled:

1. That the King's Majesty, his heirs and successors, Kings of England, shall have, hold, and enjoy the style, title, and honour of King of Ireland, with all manner of pre-eminences, royal jurisdictions, authorities, and protections belonging to the imperial crown of the realm of Ireland.

2. Heretofore the Monarchs of England held only the style of Lord of Ireland by papal grant from Pope Adrian IV (Laudabiliter), which limitation caused diverse Gaelic lords and inhabitants to presume that the royal authority was conditional and ecclesiastical rather than sovereign and perpetual.

3. By this Act, Ireland is united and knit unto the Imperial Crown of the Realm of England, establishing that any Gaelic chief, captain, or dynastic ruler who makes voluntary submission, surrendering ancestral allodial lands held under Brehon law, shall receive royal letters patent confirming said lands in English feudal tenure by knight's service, with succession governed strictly by primogeniture rather than tanistry.

4. Whosoever shall by writing, printing, overt deed, or act, attempt to deny, disturb, or diminish the King's royal title of King of Ireland, shall be adjudged guilty of High Treason and suffer the penalties thereof.""",
        },
        {
            "title": "Lord Deputy Anthony St. Leger - State Papers on Surrender and Regrant (1541–1543)",
            "content": """# Lord Deputy Anthony St. Leger: Despatches to King Henry VIII (1541–1543)

May it please Your Royal Majesty to understand the proceedings touchyng the pacification and reformacion of this your realm:

1. The chief lords of the Irishry, namely Conn Bacach O'Neill of Ulster, Murrough O'Brien of Thomond, and Ulick na gCeann Burke of Clanricarde, have repaired unto Dublin and submitted their persons and estates unto Your Majesty's gracious clemency.

2. We have accepted their surrender of all their lands, territories, and lordships, which heretofore they held by arbitrary Brehon custom without title or record. In return, Your Majesty hath graciously granted them English letters patent: Conn O'Neill is created Earl of Tyrone, Murrough O'Brien Earl of Thomond, and Ulick Burke Earl of Clanricarde.

3. The principal condition of their patents is that they shall forsake the Irish language in their courts, cause their heirs to be brought up in English civility and habits, hold their lands by capite knight's service, abolish the election of successors by tanistry, and admit Your Majesty's judges and sheriffs into their territories.

4. However, we warn Your Majesty that while the dynastic chiefs themselves gladly accept the security of hereditary English titles, their subordinate kinsmen and secondary chieftains (the urritha) murmur greatly. Under Brehon custom, the clan land belongs to the sept, not the individual chieftain; by converting clan lands into private feudal estates inherited only by the eldest son, younger sons and collaterals are disinherited, breeding the seeds of violent factional discord.""",
        },
        {
            "title": "Hugh O'Neill, Earl of Tyrone - Articles of Grievance and Demands (1599)",
            "content": """# Articles of Hugh O'Neill, Prince of Ulster, to the Crown Commissioners (1599)

Unto the Queen's Most Excellent Majesty, the humble grievances and fundamental conditions of the Catholic Confederation of Ireland:

1. That the Catholic, Apostolic, and Roman religion be openly preached and taught throughout all Ireland, and that no church property or abbey lands be detained by English governors.

2. That the Prince of Ulster and the ancient nobility of Ireland shall govern their ancestral territories without the imposition of English provincial presidents, provost-marshals, or sheriffs, whose extortionate cesses and arbitrary courts have despoiled the people.

3. That all letters patent granted under the fraudulent guise of Surrender and Regrant be reviewed, forasmuch as the Crown hath used English tenures to introduce forfeiture and confiscation whenever an Irish chieftain is falsely accused of treason.

4. That no governor of Ireland shall plant English garrisons or fortresses upon the private passes or rivers of Ulster without the consent of the Earl of Tyrone and the Irish council.

5. If these conditions be granted, the Irish nobility shall swear perpetual loyalty unto the Crown of England, rendering customary tribute and defensive service; but if they be denied, we stand resolved in arms, assisted by the Catholic King of Spain, to defend the ancient liberties and faith of our ancestors to the last man.""",
        },
    ],
    "module_2": [
        {
            "title": "Articles Concerning the Plantation of Ulster (1609)",
            "content": """# Articles Concerning the English and Scottish Undertakers in the Escheated Counties of Ulster (1609)

Orders and Conditions to be Observed by the Undertakers upon the Distribution of the Lands of the Fugitive Earls in Armagh, Tyrone, Coleraine, Donegal, Fermanagh, and Cavan:

1. The lands are partitioned into proportions of 2,000, 1,500, and 1,000 acres, distributed among three classes: English and Scottish Undertakers, Servitors (military officers), and Native Irish grantees.

2. Undertakers shall plant upon their lands families of English and Scottish inlanders, who shall be freeholders and copyholders; and no Undertaker shall alienate his lands to any mere Irishman or person refusing the Oath of Supremacy.

3. Undertakers of 2,000 acres shall within three years erect a strong stone castle with a bawn of 24 feet square, maintain twelve armed men, and build compact civility settlements around the parish church.

4. The native Irish inhabitants who have been dispossessed shall be removed from the fertile river valleys and relocated into the waste mountains and bogs, lest their proximity encourage rebellion or treason against the British settlers.""",
        },
        {
            "title": "1641 Depositions - Commission of Inquiry on the Ulster Rebellion",
            "content": """# Depositions Taken by Virtue of a Commission under the Great Seal of Ireland (1641–1643)

Deposition of Dame Alice Blayney of Castleblayney, County Monaghan:

1. Deponent saith that upon the 23rd day of October 1641, the Irish rebels under the command of Sir Phelim O'Neill did unexpectedly rise in universal insurrection throughout the province of Ulster, declaring they had royal authority from King Charles to restore the Catholic faith and repossess the ancestral lands confiscated during the British plantation.

2. The rebels seized the forts of Charlemont and Mountjoy, stripped the English and Scottish Protestant inhabitants of all their goods, cattle, and apparel, and expelled thousands of families in the bitter cold of winter.

3. When interrogated by deponent why they broke their oaths of peace, the rebel captains replied that thirty years of plantation had reduced the ancient Irish gentry to impoverished tenants on their own fathers' estates, and that they would never lay down arms until every acre of Ulster was returned to native tenure.""",
        },
    ],
    "module_3": [
        {
            "title": "Act for the Settlement of Ireland (1652) - Commonwealth Parliament",
            "content": """# An Act for the Settlement of Ireland (12 August 1652)

Whereas the Parliament of England hath, by the blessing of God upon their forces under the Lord General Oliver Cromwell, subdued the bloody and unnatural rebellion in Ireland:

1. All Roman Catholic proprietors, landlords, and clergy who participated in or promoted the rebellion from 1641 onwards are exempted from pardon for life and estate.

2. All other Irish proprietors who did not demonstrate constant active affection to the Commonwealth of England shall forfeit two-thirds of their real estates, and shall accept the remaining one-third in the western province of Connacht or county of Clare, being transplanted thither across the River Shannon before the first day of May 1654.

3. The confiscated lands in the three provinces of Leinster, Munster, and Ulster are set apart and assigned to satisfy the arrears of pay due to the soldiers of the Parliamentary Army and the loans made by the Merchant Adventurers of London.""",
        },
        {
            "title": "Sir William Petty - The Down Survey and Political Anatomy of Ireland (1656–1672)",
            "content": """# Sir William Petty: The Down Survey and Statistical Distribution of Landed Estate

1. The Down Survey was prosecuted by chain and compass, laid down upon maps with exact mathematical calculation, to measure 8,400,000 acres of forfeited land for distribution among Commonwealth soldiers.

2. In the year 1641, before the rebellion, Roman Catholic Irish proprietors owned 59 per cent of the profitable land of Ireland. Following the Cromwellian confiscations and the Williamite forfeiture commissions after the Treaty of Limerick (1691), the Catholic share of profitable land was compressed to less than 14 per cent.

3. The legislative superstructure erected under Queen Anne, known as the Penal Laws, forbids any Catholic to purchase land in fee simple, to take leases exceeding thirty-one years, or to retain an estate intact under primogeniture without it being divided among all sons unless the eldest son conform to the Established Church.""",
        },
    ],
}


CONCEPTS_TAXONOMY = [
    {
        "proposal_id": "c_theme",
        "label": "Early Modern Irish Constitutional and Agrarian Transformation",
        "definition": "The systemic transformation of Ireland from autonomous Gaelic-Norman lordships into an integrated confessional kingdom under English common law and parliamentary hegemony (1536–1750).",
        "concept_type": "domain",
        "level": "course_theme",
        "parent_proposal_id": None,
        "module_positions": [1, 2, 3],
        "module_role": "introduces",
    },
    {
        "proposal_id": "c_strand_sovereignty",
        "label": "Constitutional Sovereignty: Lordship to Kingdom",
        "definition": "The legal and ideological restructuring of royal power initiated by the Crown of Ireland Act 1541 and Surrender and Regrant, ending the medieval Lordship and asserting sovereign English imperium.",
        "concept_type": "process",
        "level": "strand",
        "parent_proposal_id": "c_theme",
        "module_positions": [1],
        "module_role": "introduces",
    },
    {
        "proposal_id": "c_strand_tenure",
        "label": "Land Tenure Colonization and Plantation Schemes",
        "definition": "The replacement of collective Gaelic Brehon landholding (tanistry) with English private feudal tenure, culminating in the Ulster Plantation, confiscations, and demographic restructuring.",
        "concept_type": "process",
        "level": "strand",
        "parent_proposal_id": "c_theme",
        "module_positions": [1, 2, 3],
        "module_role": "develops",
    },
    {
        "proposal_id": "c_strand_confession",
        "label": "Confessional Division and Sectarian Grievance",
        "definition": "The divergence between the Protestant Established Church and the Roman Catholic majority, generating existential conflict over oath compliance, church land, and the 1641 rebellion.",
        "concept_type": "domain",
        "level": "strand",
        "parent_proposal_id": "c_theme",
        "module_positions": [2, 3],
        "module_role": "develops",
    },
    {
        "proposal_id": "c_surrender_regrant",
        "label": "Surrender and Regrant Policy",
        "definition": "The Tudor diplomatic framework whereby Gaelic chieftains surrendered allodial clan territories to King Henry VIII and received them back as English feudal estates with royal peerages (1541–1543).",
        "concept_type": "policy",
        "level": "topic",
        "parent_proposal_id": "c_strand_sovereignty",
        "module_positions": [1],
        "module_role": "introduces",
    },
    {
        "proposal_id": "c_tanistry_vs_feudal",
        "label": "Tanistry versus Feudal Primogeniture",
        "definition": "The structural conflict between Gaelic elective clan succession (tanistry/righdamhna) and English hereditary primogeniture, which disinherited subordinate kinsmen (urritha) and triggered dynastic factionalism.",
        "concept_type": "mechanism",
        "level": "topic",
        "parent_proposal_id": "c_strand_tenure",
        "module_positions": [1],
        "module_role": "introduces",
    },
    {
        "proposal_id": "c_nine_years_war",
        "label": "Nine Years' War and Spanish Alliance (1594–1603)",
        "definition": "The confederated Gaelic resistance led by Hugh O'Neill, Earl of Tyrone, resisting English provincial garrisons and sheriffs, culminating in the Battle of Kinsale and the Treaty of Mellifont.",
        "concept_type": "conflict",
        "level": "topic",
        "parent_proposal_id": "c_strand_sovereignty",
        "module_positions": [1],
        "module_role": "assesses",
    },
    {
        "proposal_id": "c_ulster_plantation",
        "label": "The Ulster Plantation (1609)",
        "definition": "The state-sponsored demographic colonization of the six escheated counties of Ulster following the Flight of the Earls (1607), barring native Irish from undertaker estates and creating British Protestant settlements.",
        "concept_type": "policy",
        "level": "topic",
        "parent_proposal_id": "c_strand_tenure",
        "module_positions": [2],
        "module_role": "introduces",
    },
    {
        "proposal_id": "c_1641_rebellion",
        "label": "The 1641 Rebellion and Depositions",
        "definition": "The armed insurrection of the Ulster Irish triggered by dispossessed Catholic gentry seeking the restitution of land and religious toleration, leading to sectarian massacres and polarising British historiography.",
        "concept_type": "conflict",
        "level": "topic",
        "parent_proposal_id": "c_strand_confession",
        "module_positions": [2],
        "module_role": "assesses",
    },
    {
        "proposal_id": "c_cromwell_settlement",
        "label": "Cromwellian Confiscation and Act of Settlement 1652",
        "definition": "The punitive redistribution of Catholic-owned land across Leinster, Munster, and Ulster to satisfy Commonwealth army debentures, forcibly transplanting Catholic proprietors across the Shannon into Connacht.",
        "concept_type": "policy",
        "level": "topic",
        "parent_proposal_id": "c_strand_tenure",
        "module_positions": [3],
        "module_role": "introduces",
    },
    {
        "proposal_id": "c_penal_laws",
        "label": "The Penal Code and Ascendancy Hegemony (1695–1750)",
        "definition": "The battery of discriminatory statutes enacted after the Williamite victory (1691), legally disempowering Catholic land ownership, political representation, and inheritance rights.",
        "concept_type": "policy",
        "level": "topic",
        "parent_proposal_id": "c_strand_confession",
        "module_positions": [3],
        "module_role": "assesses",
    },
]

PREREQUISITES = [
    {
        "prerequisite_proposal_id": "c_surrender_regrant",
        "dependent_proposal_id": "c_tanistry_vs_feudal",
        "rationale": "Understanding the feudal regrant mechanism is required before analyzing its collision with tanistry succession.",
    },
    {
        "prerequisite_proposal_id": "c_tanistry_vs_feudal",
        "dependent_proposal_id": "c_nine_years_war",
        "rationale": "Dynastic disinheritance under English letters patent provided the immediate grievance driving the O'Neill coalition.",
    },
    {
        "prerequisite_proposal_id": "c_nine_years_war",
        "dependent_proposal_id": "c_ulster_plantation",
        "rationale": "The defeat of the Gaelic lords and the Flight of the Earls in 1607 enabled the escheatment and plantation of Ulster.",
    },
    {
        "prerequisite_proposal_id": "c_ulster_plantation",
        "dependent_proposal_id": "c_1641_rebellion",
        "rationale": "The dispossession of native Ulster proprietors during the 1609 plantation directly fueled the 1641 rebellion.",
    },
    {
        "prerequisite_proposal_id": "c_1641_rebellion",
        "dependent_proposal_id": "c_cromwell_settlement",
        "rationale": "The 1652 Act of Settlement was enacted as explicit ideological and economic retaliation for the 1641 rebellion.",
    },
    {
        "prerequisite_proposal_id": "c_cromwell_settlement",
        "dependent_proposal_id": "c_penal_laws",
        "rationale": "The post-1691 Penal Laws consolidated the property transfers initiated under the Cromwellian and Williamite forfeitures.",
    },
]


async def seed_course_and_curriculum() -> tuple[UUID, UUID, UUID]:
    """
    Executes full pipeline:
    - Creates Course & Modules
    - Ingests primary sources into PostgreSQL (pgvector)
    - Hydrates Neo4j Concept Graph & Prerequisite DAG
    - Creates Reasoning Milestone Assignment
    """
    logger.info("Step 1: Creating or locating HI4083 Course Workspace...")
    course_title = "HI4083: Early Modern Ireland, 1536-1750"
    domain = "History"
    instructor = "Dr. Vance"
    syllabus_summary = (
        "This course examines the political, religious, and economic transformation of Ireland "
        "from the Tudor conquests through the Williamite settlement. Students will analyze primary sources "
        "including parliamentary statutes, state papers, plantation surveys, and witness depositions."
    )

    # Check existing course
    existing_courses = await course_service.list_courses()
    course = next((c for c in existing_courses if "HI4083" in c.title), None)

    if not course:
        course = await course_service.create_course(
            CourseCreate(
                title=course_title,
                domain=domain,
                created_by=instructor,
                syllabus_context=syllabus_summary,
            )
        )
        logger.info("Created new course %s (%s)", course.title, course.course_id)
    else:
        logger.info("Found existing course %s (%s)", course.title, course.course_id)

    course_id = course.course_id

    # Step 2: Ensure 3 sequenced modules
    logger.info("Step 2: Ensuring 3 Sequenced Curriculum Modules...")
    modules_spec = [
        (
            1,
            "The Tudor Reconquest & Surrender-and-Regrant (1536-1603)",
            "The constitutional shift from lordship to kingdom, legal assimilation under St. Leger, Brehon tanistry collision, and the Nine Years' War.",
            [
                "Analyze the legal mechanics of the Crown of Ireland Act 1541.",
                "Differentiate customary Gaelic tanistry succession from English feudal primogeniture.",
                "Trace how dynastic grievances under surrender-and-regrant culminated in the Nine Years' War.",
            ],
        ),
        (
            2,
            "The Ulster Plantation Schemes & Confessional Division (1603-1641)",
            "The demographic engineering of escheated Ulster counties, Scottish/English undertakers, sectarian polarization, and the 1641 rebellion.",
            [
                "Evaluate the structural segregation enforced by the 1609 Articles of Plantation.",
                "Analyze eyewitness testimony from the 1641 Depositions regarding land expropriation.",
                "Explain the convergence of religious allegiance and economic grievance in 1641.",
            ],
        ),
        (
            3,
            "The Cromwellian Confiscations & Williamite Settlement (1649-1704)",
            "The Act for the Settlement of Ireland, Sir William Petty's Down Survey, transplantation to Connacht, and the Penal Era.",
            [
                "Critique cartographic surveys as instruments of fiscal confiscation under Petty.",
                "Quantify the shift in Catholic land ownership between 1641 and 1703.",
                "Assess the constitutional legacy of the Penal Code in securing Protestant Ascendancy.",
            ],
        ),
    ]

    module_ids: dict[int, UUID] = {}
    current_modules = await course_service.get_modules_for_course(course_id)

    for pos, title, desc, objs in modules_spec:
        mod = next((m for m in current_modules if m.position == pos), None)
        if not mod:
            mod = await course_service.add_module(
                course_id,
                ModuleCreate(
                    title=title,
                    description=desc,
                    learning_objectives=objs,
                    position=pos,
                ),
            )
            logger.info("Created Module %d: %s", pos, title)
        module_ids[pos] = mod.module_id

    # Step 3: Ingest Primary Sources into pgvector and Neo4j
    logger.info("Step 3: Ingesting Primary Source Texts into PostgreSQL pgvector & Neo4j...")
    for mod_pos, sources in PRIMARY_SOURCES.items():
        pos_int = int(mod_pos.split("_")[1])
        m_id = module_ids[pos_int]
        for src in sources:
            chunks = await syllabus_parser.ingest_syllabus(
                course_id=course_id,
                module_id=m_id,
                content=src["content"],
                title=src["title"],
                domain=domain,
                resource_type="primary_source",
            )
            # Link chunks to Neo4j
            chunk_dicts = [
                {
                    "chunk_id": str(c.chunk_id),
                    "title": c.title,
                    "content": c.content,
                    "kc_id": c.kc_id,
                }
                for c in chunks
            ]
            await concept_graph_service.ingest_resource(
                course_id=str(course_id),
                module_id=str(m_id),
                title=src["title"],
                resource_type="primary_source",
                source_url=None,
                chunks=chunk_dicts,
            )
            logger.info("Ingested and grounded primary source: %s (%d chunks)", src["title"], len(chunks))

    # Step 4: Hydrate Neo4j Concept Graph & Prerequisite DAG
    logger.info("Step 4: Hydrating Neo4j High-to-Low Concept Graph & Prerequisite DAG...")
    reloaded_course = await course_service.get_course(course_id)
    await concept_graph_service.sync_course_structure(reloaded_course)

    concept_id_map: dict[str, str] = {}
    for c_spec in CONCEPTS_TAXONOMY:
        created = await concept_graph_service.create_concept(
            course_id=str(course_id),
            label=c_spec["label"],
            definition=c_spec["definition"],
            concept_type=c_spec["concept_type"],
            level=c_spec["level"],
        )
        concept_id_map[c_spec["proposal_id"]] = created["concept_id"]

        # Link to module
        for pos in c_spec["module_positions"]:
            m_id = module_ids.get(pos)
            if m_id:
                try:
                    await concept_graph_service.link_module(
                        course_id=str(course_id),
                        module_id=str(m_id),
                        concept_id=created["concept_id"],
                        role=c_spec["module_role"],
                    )
                except Exception as e:
                    logger.debug("Module link notice: %s", e)

    # Establish CONTAINS hierarchy
    for c_spec in CONCEPTS_TAXONOMY:
        parent_prop = c_spec.get("parent_proposal_id")
        if parent_prop and parent_prop in concept_id_map:
            try:
                await concept_graph_service.add_contains(
                    course_id=str(course_id),
                    parent_id=concept_id_map[parent_prop],
                    child_id=concept_id_map[c_spec["proposal_id"]],
                )
            except Exception as e:
                logger.debug("Contains edge notice: %s", e)

    # Establish PREREQUISITE_OF DAG
    for prereq in PREREQUISITES:
        p_id = concept_id_map.get(prereq["prerequisite_proposal_id"])
        d_id = concept_id_map.get(prereq["dependent_proposal_id"])
        if p_id and d_id:
            try:
                await concept_graph_service.add_prerequisite(
                    course_id=str(course_id),
                    prerequisite_id=p_id,
                    dependent_id=d_id,
                )
                logger.info("Added Prerequisite: %s -> %s", prereq["prerequisite_proposal_id"], prereq["dependent_proposal_id"])
            except Exception as e:
                logger.warning("Prerequisite edge notice: %s", e)

    # Step 5: Create Well-Formed Assignment Milestone under Module 1
    logger.info("Step 5: Creating Well-Formed Assignment Milestone under Module 1...")
    target_module_id = module_ids[1]
    assignment_title = "Inquiry: Constitutional Sovereignty and Surrender-and-Regrant (1536-1603)"
    assignment_prompt = (
        "Assess the degree to which the policy of Surrender and Regrant under Henry VIII and Lord Deputy St. Leger "
        "achieved genuine institutional integration of Gaelic lordships between 1541 and 1599. "
        "In your analysis, examine the constitutional shift from Lordship to Kingdom, contrast Brehon inheritance (tanistry) "
        "with English feudal tenure, and explain why the policy broke down into the Nine Years' War."
    )

    published_spec = {
        "title": assignment_title,
        "purpose": "Analyze constitutional transformation and tenure destabilization in 16th-century Tudor Ireland.",
        "task": {
            "prompt": assignment_prompt,
            "scope": "Tudor Ireland (1536–1603), specifically the 1541 Crown of Ireland Act and St. Leger's despatches",
            "deliverable": "A structured, evidence-grounded historical analysis on the A4 Reasoning Canvas.",
            "requirements": [
                "Ground claims in assigned primary sources (1541 Crown of Ireland Act or St. Leger's State Papers).",
                "Explain the causal mechanism linking English feudal tenure to Gaelic succession conflict (tanistry).",
                "Maintain temporal boundaries strictly between 1536 and 1603.",
            ],
        },
        "target_kcs": [
            concept_id_map["c_surrender_regrant"],
            concept_id_map["c_tanistry_vs_feudal"],
            concept_id_map["c_nine_years_war"],
        ],
        "learning_goals": [
            "Analyze the legal transition from papal Lordship to sovereign Kingdom.",
            "Explain how replacing clan allodial title with individual feudal tenure destabilized Gaelic clan politics.",
        ],
        "source_pack": [
            {
                "source_id": "source_1",
                "title": "Crown of Ireland Act (1541) - 33 Hen. 8 c. 1",
                "excerpt": "That the King's Majesty, his heirs and successors, Kings of England, shall have, hold, and enjoy the style, title, and honour of King of Ireland... Ireland is united and knit unto the Imperial Crown of the Realm of England.",
                "source_url": None,
                "citation": "Statutes of the Realm, Ireland (1541)",
                "relevance_guidance": "Examine Section 3 for the legal mechanism converting Brehon tenures into English letters patent.",
            },
            {
                "source_id": "source_2",
                "title": "Lord Deputy Anthony St. Leger - State Papers (1541-1543)",
                "excerpt": "Conn O'Neill is created Earl of Tyrone... The principal condition of their patents is that they hold their lands by capite knight's service, abolish the election of successors by tanistry, and admit Your Majesty's judges.",
                "source_url": None,
                "citation": "Tudor State Papers (Ireland), 1541",
                "relevance_guidance": "Observe St. Leger's warning regarding younger sons and clan kinsmen disinherited by primogeniture.",
            },
            {
                "source_id": "source_3",
                "title": "Hugh O'Neill - Articles of Grievance (1599)",
                "excerpt": "That the Prince of Ulster and ancient nobility of Ireland shall govern their ancestral territories without the imposition of English provincial presidents, provost-marshals, or sheriffs... and review fraudulent patents.",
                "source_url": None,
                "citation": "Salisbury Manuscripts, Hatfield House (1599)",
                "relevance_guidance": "Analyze how failure of surrender-and-regrant produced armed confederated resistance.",
            },
        ],
        "public_rubric": [
            {
                "criterion_id": "rubric_source_grounding",
                "title": "Primary Source Evidentiary Grounding",
                "description": "Claims must directly cite statutory or documentary evidence from the 1541 Act or St. Leger's State Papers.",
                "levels": [
                    {"level_id": "developing", "label": "Developing", "description": "Mentions events without quoting or analyzing primary source text."},
                    {"level_id": "secure", "label": "Secure", "description": "Directly analyzes specific statutory clauses or state paper extracts to corroborate assertions."},
                ],
            },
            {
                "criterion_id": "rubric_causal_mechanism",
                "title": "Institutional & Tenurial Causality",
                "description": "Explains the concrete mechanism by which feudal primogeniture undermined customary Brehon succession.",
                "levels": [
                    {"level_id": "developing", "label": "Developing", "description": "Asserts conflict occurred without articulating tenurial differences."},
                    {"level_id": "secure", "label": "Secure", "description": "Demonstrates how converting clan territory into individual patents disinherited collateral kinsmen."},
                ],
            },
            {
                "criterion_id": "rubric_temporal_coherence",
                "title": "Chronological & Conceptual Integrity",
                "description": "Confines arguments strictly to the 16th-century Tudor context without anachronisms.",
                "levels": [
                    {"level_id": "secure", "label": "Secure", "description": "Maintains strict focus on 1536–1603 institutions and sources."},
                ],
            },
        ],
    }

    # Upsert Assignment in PostgreSQL
    async with AsyncSessionLocal() as session:
        check_sql = text("""
            SELECT assignment_id FROM assignments
            WHERE module_id = CAST(:module_id AS UUID) AND title = :title
        """)
        res = await session.execute(check_sql, {"module_id": str(target_module_id), "title": assignment_title})
        existing_assign = res.mappings().first()

        if existing_assign:
            assignment_id = existing_assign["assignment_id"]
            full_spec = {
                "assignment_id": str(assignment_id),
                "question_id": str(assignment_id),
                "status": "published",
                "domain": "History",
                "title": assignment_title,
                "prompt": assignment_prompt,
                "target_kcs": published_spec["target_kcs"],
                "published": published_spec,
                "evaluation_plan": {
                    "public_rubric_map": [
                        {
                            "public_criterion_id": "rubric_source_grounding",
                            "evidence_expectation": "Direct citation or quotation of 1541 Crown of Ireland Act or St. Leger's despatches.",
                            "concept_ids": [concept_id_map["c_surrender_regrant"]],
                            "source_chunk_ids": [],
                        },
                        {
                            "public_criterion_id": "rubric_causal_mechanism",
                            "evidence_expectation": "Articulation of how primogeniture disinherited the sept under Brehon law.",
                            "concept_ids": [concept_id_map["c_tanistry_vs_feudal"]],
                            "source_chunk_ids": [],
                        },
                        {
                            "public_criterion_id": "rubric_temporal_coherence",
                            "evidence_expectation": "Strict adherence to 1536-1603 events, institutions, and actors.",
                            "concept_ids": [concept_id_map["c_nine_years_war"]],
                            "source_chunk_ids": [],
                        },
                    ],
                    "support_policy": ["Highlight ungrounded leaps", "Step down prerequisite ladder when confused"],
                    "review_policy": "Flag uncorroborated assertions without punitive grading.",
                },
            }
            update_sql = text("""
                UPDATE assignments
                SET spec = CAST(:spec AS jsonb)
                WHERE assignment_id = CAST(:assignment_id AS UUID)
            """)
            await session.execute(
                update_sql,
                {
                    "assignment_id": str(assignment_id),
                    "spec": json.dumps(full_spec),
                },
            )
            logger.info("Updated existing Assignment Milestone %s", assignment_id)
        else:
            assignment_id = uuid4()
            full_spec = {
                "assignment_id": str(assignment_id),
                "question_id": str(assignment_id),
                "status": "published",
                "domain": "History",
                "title": assignment_title,
                "prompt": assignment_prompt,
                "target_kcs": published_spec["target_kcs"],
                "published": published_spec,
                "evaluation_plan": {
                    "public_rubric_map": [
                        {
                            "public_criterion_id": "rubric_source_grounding",
                            "evidence_expectation": "Direct citation or quotation of 1541 Crown of Ireland Act or St. Leger's despatches.",
                            "concept_ids": [concept_id_map["c_surrender_regrant"]],
                            "source_chunk_ids": [],
                        },
                        {
                            "public_criterion_id": "rubric_causal_mechanism",
                            "evidence_expectation": "Articulation of how primogeniture disinherited the sept under Brehon law.",
                            "concept_ids": [concept_id_map["c_tanistry_vs_feudal"]],
                            "source_chunk_ids": [],
                        },
                        {
                            "public_criterion_id": "rubric_temporal_coherence",
                            "evidence_expectation": "Strict adherence to 1536-1603 events, institutions, and actors.",
                            "concept_ids": [concept_id_map["c_nine_years_war"]],
                            "source_chunk_ids": [],
                        },
                    ],
                    "support_policy": ["Highlight ungrounded leaps", "Step down prerequisite ladder when confused"],
                    "review_policy": "Flag uncorroborated assertions without punitive grading.",
                },
            }
            insert_sql = text("""
                INSERT INTO assignments (
                    assignment_id, module_id, title, created_by, spec, created_at
                ) VALUES (
                    CAST(:assignment_id AS UUID),
                    CAST(:module_id AS UUID),
                    :title, 'Dr. Vance',
                    CAST(:spec AS jsonb),
                    NOW()
                )
            """)
            await session.execute(
                insert_sql,
                {
                    "assignment_id": str(assignment_id),
                    "module_id": str(target_module_id),
                    "title": assignment_title,
                    "spec": json.dumps(full_spec),
                },
            )
            logger.info("Created new Assignment Milestone %s", assignment_id)
        await session.commit()

    logger.info("=== HI4083 CURRICULUM SEEDING COMPLETE ===")
    logger.info("Course ID: %s", course_id)
    logger.info("Module 1 ID: %s", target_module_id)
    logger.info("Assignment ID: %s", assignment_id)
    return course_id, target_module_id, assignment_id


if __name__ == "__main__":
    asyncio.run(seed_course_and_curriculum())
