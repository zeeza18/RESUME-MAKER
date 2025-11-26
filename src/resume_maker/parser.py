"""Parse tailored resume text into structured data."""

from __future__ import annotations

from typing import Dict, List

from .text_utils import cleanse_line, convert_links, dedupe_list, is_section_heading, to_ascii


def parse_resume_text(raw_text: str) -> Dict[str, object]:
    main_text = raw_text.split("### Change Log", 1)[0]
    lines = [line.strip() for line in main_text.splitlines()]
    filtered: List[str] = []
    for line in lines:
        if not line or line.startswith("===") or line.startswith("###") or line.upper().startswith("TAILORED RESUME"):
            continue
        filtered.append(line)

    if len(filtered) < 2:
        raise ValueError("Resume text appears to be empty after cleaning")

    name_line = filtered[0]
    contact_line = filtered[1]
    name = cleanse_line(name_line)
    contacts_raw = convert_links(to_ascii(contact_line))
    contact_parts = [part.strip() for part in contacts_raw.split('|') if part.strip()]
    tagline = contact_parts[0] if contact_parts else ''
    contact_details = contact_parts[1:] if len(contact_parts) > 1 else []

    sections: Dict[str, List[Dict[str, str]]] = {
        'education': [],
        'experience': [],
        'projects': [],
        'skills': [],
    }

    current_section: str | None = None
    idx = 2
    total_lines = len(filtered)

    while idx < total_lines:
        line = filtered[idx]
        if line == '---':
            idx += 1
            continue

        if is_section_heading(line):
            section_name = line.strip('*').strip().lower()
            section_key = section_name.split()[0]
            if section_key.startswith('education'):
                current_section = 'education'
            elif section_key.startswith('experience'):
                current_section = 'experience'
            elif section_key.startswith('project'):
                current_section = 'projects'
            elif section_key.startswith('skill'):
                current_section = 'skills'
            else:
                current_section = None
            idx += 1
            continue

        if not current_section:
            idx += 1
            continue

        if current_section == 'education':
            entry, new_idx = _parse_education_entry(filtered, idx)
            sections['education'].append(entry)
            idx = new_idx
            continue

        if current_section == 'experience':
            entry, new_idx = _parse_experience_entry(filtered, idx)
            sections['experience'].append(entry)
            idx = new_idx
            continue

        if current_section == 'projects':
            entry, new_idx = _parse_project_entry(filtered, idx)
            sections['projects'].append(entry)
            idx = new_idx
            continue

        if current_section == 'skills':
            entry, new_idx = _parse_skills_entry(filtered, idx)
            sections['skills'].extend(entry)
            idx = new_idx
            continue

        idx += 1

    sections['experience'] = dedupe_list(
        sections['experience'],
        key_fn=lambda r: (r['title'], r['company'], tuple(r.get('bullets', []))),
    )
    sections['projects'] = dedupe_list(
        sections['projects'],
        key_fn=lambda p: (p['name'], tuple(p.get('bullets', []))),
    )

    return {
        'name': name,
        'tagline': tagline,
        'contacts': contact_details,
        'sections': sections,
    }


def _parse_education_entry(lines: List[str], start_idx: int) -> tuple[Dict[str, str], int]:
    institution = cleanse_line(lines[start_idx])
    degree = cleanse_line(lines[start_idx + 1]) if start_idx + 1 < len(lines) else ''
    details_line = cleanse_line(lines[start_idx + 2]) if start_idx + 2 < len(lines) else ''

    location = ''
    dates = ''
    if '|' in details_line:
        parts = [part.strip() for part in details_line.split('|')]
        if parts:
            location = parts[0]
        if len(parts) > 1:
            dates = parts[1]
    else:
        location = details_line

    entry = {
        'institution': institution,
        'degree': degree,
        'location': location,
        'dates': dates,
    }
    return entry, start_idx + 3


def _parse_experience_entry(lines: List[str], start_idx: int) -> tuple[Dict[str, object], int]:
    title_line = cleanse_line(lines[start_idx])
    company_line = cleanse_line(lines[start_idx + 1]) if start_idx + 1 < len(lines) else ''

    title = title_line
    dates = ''
    if '|' in title_line:
        parts = [part.strip() for part in title_line.split('|')]
        title = parts[0]
        if len(parts) > 1:
            dates = parts[1]

    company = company_line
    location = ''
    if '|' in company_line:
        parts = [part.strip() for part in company_line.split('|')]
        company = parts[0]
        if len(parts) > 1:
            location = parts[1]

    bullets: List[str] = []
    idx = start_idx + 2
    while idx < len(lines):
        candidate = lines[idx].strip()
        if not candidate or candidate == '---' or is_section_heading(candidate):
            break
        if candidate.startswith('- '):
            bullets.append(cleanse_line(candidate))
        idx += 1

    entry: Dict[str, object] = {
        'title': title,
        'dates': dates,
        'company': company,
        'location': location,
        'bullets': bullets,
    }
    return entry, idx


def _parse_project_entry(lines: List[str], start_idx: int) -> tuple[Dict[str, object], int]:
    name_line = cleanse_line(lines[start_idx])
    details_line = cleanse_line(lines[start_idx + 1]) if start_idx + 1 < len(lines) else ''

    name = name_line
    dates = ''
    if '|' in name_line:
        parts = [part.strip() for part in name_line.split('|')]
        name = parts[0]
        if len(parts) > 1:
            dates = parts[1]

    details = details_line
    idx = start_idx + 2
    bullets: List[str] = []
    while idx < len(lines):
        candidate = lines[idx].strip()
        if not candidate or candidate == '---' or is_section_heading(candidate):
            break
        if candidate.startswith('- '):
            bullets.append(cleanse_line(candidate))
        idx += 1

    entry: Dict[str, object] = {
        'name': name,
        'dates': dates,
        'details': details,
        'bullets': bullets,
    }
    return entry, idx


def _parse_skills_entry(lines: List[str], start_idx: int) -> tuple[List[Dict[str, str]], int]:
    skills: List[Dict[str, str]] = []
    idx = start_idx
    while idx < len(lines):
        candidate = lines[idx].strip()
        if not candidate or candidate == '---' or is_section_heading(candidate):
            break
        cleaned = cleanse_line(candidate)
        if ':' in cleaned:
            category, items = [part.strip() for part in cleaned.split(':', 1)]
        else:
            category, items = '', cleaned
        skills.append({'category': category, 'items': items})
        idx += 1
    return skills, idx
