from typing import List, Optional
from app.repositories.report_title_repository import ReportTitleRepository
from app.database.models import ReportTitle


class ReportTitleService:
    def __init__(self, report_title_repository: ReportTitleRepository):
        self._repository = report_title_repository

    def get_all_titles(self) -> List[ReportTitle]:
        return self._repository.find_all()

    def get_all_title_texts(self) -> List[str]:
        titles = self.get_all_titles()
        return [title.title_text for title in titles]

    def get_default_title(self) -> str:
        titles = self.get_all_titles()
        return titles[0].title_text if titles else ""

    def get_title_by_id(self, title_id: int) -> Optional[ReportTitle]:
        return self._repository.find_by_id(title_id)

    def create_title(self, title_text: str) -> ReportTitle:
        if not title_text.strip():
            raise ValueError("Title text cannot be empty")

        # Check for duplicates
        existing_title = self._repository.find_by_title_text(title_text.strip())
        if existing_title:
            raise ValueError(f"Title '{title_text}' already exists")

        title = ReportTitle(title_text=title_text.strip())
        return self._repository.create(title)

    def update_title(self, title_id: int, new_title_text: str) -> ReportTitle:
        if not new_title_text.strip():
            raise ValueError("Title text cannot be empty")

        title = self._repository.find_by_id(title_id)
        if not title:
            raise ValueError(f"Report title with ID {title_id} not found")

        # Check for duplicates (excluding current title)
        existing_title = self._repository.find_by_title_text(new_title_text.strip())
        if existing_title and existing_title.id != title_id:
            raise ValueError(f"Title '{new_title_text}' already exists")

        title.title_text = new_title_text.strip()
        return self._repository.update(title)

    def delete_title(self, title_id: int) -> bool:
        all_titles = self.get_all_titles()

        if len(all_titles) <= 1:
            raise ValueError("Cannot delete the last remaining title")

        return self._repository.delete(title_id)

    def get_statistics(self) -> dict:
        titles = self.get_all_titles()
        return {
            'total_titles': len(titles),
            'default_title': self.get_default_title()
        }