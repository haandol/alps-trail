"""
ALPS Document Parser Module

This module implements the functionality to parse ALPS documents and extract
Section 6 (Feature-Level Specification) using LLM-based analysis.
"""

import asyncio
import logging
import traceback
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from botocore.config import Config
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Enumeration for dependency types between features/tasks."""
    STRONG = "strong"
    WEAK = "weak"
    NONE = "none"


class ALPSSubsection(BaseModel):
    """Represents a subsection within Section 6 of an ALPS document."""
    subsection_number: str = Field(..., description="Subsection number (e.g., '6.1')")
    subsection_title: str = Field(..., description="Subsection title")
    content: str = Field(..., description="Raw content of the subsection")
    user_story: str = Field(default="", description="Extracted user story")
    technical_description: str = Field(default="", description="Technical implementation details")
    complexity: Optional[str] = Field(default=None, description="Complexity level (Easy, Medium, Hard)")


class ALPSSection(BaseModel):
    """Represents a section of an ALPS document."""
    section_number: str = Field(..., description="Section number (e.g., '6')")
    section_title: str = Field(..., description="Section title")
    content: str = Field(..., description="Raw content of the section")
    subsections: List[ALPSSubsection] = Field(default_factory=list, description="List of subsections")


class ALPSDocument(BaseModel):
    """Represents a complete ALPS document."""
    sections: Dict[str, ALPSSection] = Field(default_factory=dict, description="Dictionary of sections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class ALPSParseError(Exception):
    """Custom exception for ALPS parsing errors."""
    pass


class ALPSParser:
    """
    Parser for ALPS documents with LLM-based section extraction.

    This class handles the parsing of ALPS documents, specifically focusing on
    extracting Section 6 (Feature-Level Specification) and structuring the content
    for further processing.
    """

    def __init__(self) -> None:
        """Initialize the ALPS parser with Claude 3.7 Sonnet model."""
        try:
            config = Config(
                region_name="us-west-2",
                read_timeout=300,  # 5 minutes
                connect_timeout=60,  # 1 minute for connection
            )
            self.llm = ChatBedrockConverse(
                model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                temperature=0.0,
                max_tokens=1024*16,
                config=config,
            )
            logger.info("ALPS Parser initialized successfully with Claude 3.7 Sonnet 🚀")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {traceback.format_exc()}")
            raise ALPSParseError(f"Failed to initialize LLM: {str(e)}")

    def read_alps_document(self, file_path: str) -> str:
        """
        Read ALPS document from file path.

        Args:
            file_path (str): Path to the ALPS markdown document

        Returns:
            str: Content of the document

        Raises:
            ALPSParseError: If file cannot be read or doesn't exist
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise ALPSParseError(f"File not found: {file_path}")

            if not path.suffix.lower() in ['.md', '.markdown', '.txt']:
                logger.warning(f"File extension {path.suffix} may not be a markdown file")

            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            content = None

            for encoding in encodings:
                try:
                    with open(path, 'r', encoding=encoding) as file:
                        content = file.read()
                    logger.info(f"Successfully read file with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                raise ALPSParseError(f"Could not decode file with any supported encoding")

            if not content.strip():
                raise ALPSParseError("Document is empty")

            logger.info(f"Successfully read ALPS document: {len(content)} characters 📄")
            return content

        except Exception as e:
            logger.error(f"Error reading ALPS document: {traceback.format_exc()}")
            raise ALPSParseError(f"Failed to read document: {str(e)}")

    async def extract_section_6(self, content: str) -> str:
        """
        Extract Section 6 from ALPS document using simple section splitting.

        Args:
            content (str): Full content of the ALPS document

        Returns:
            str: Extracted Section 6 content

        Raises:
            ALPSParseError: If Section 6 cannot be found or extracted
        """
        try:
            logger.info("Extracting Section 6 using section splitting...")

            # Split document by section delimiter
            sections = content.split('\n---\n')

            # Check if we have at least 6 sections (index 5 for 6th section)
            if len(sections) < 6:
                raise ALPSParseError(f"Document contains only {len(sections)} sections, Section 6 not found")

            # Get the 6th section (index 5)
            section_6_content = sections[5].strip()

            if not section_6_content:
                raise ALPSParseError("Section 6 content is empty")

            logger.info(f"Successfully extracted Section 6: {len(section_6_content)} characters ✅")
            return section_6_content

        except ALPSParseError:
            raise
        except Exception as e:
            logger.error(f"Error extracting Section 6: {traceback.format_exc()}")
            raise ALPSParseError(f"Failed to extract Section 6: {str(e)}")

    async def parse_subsections(self, section_content: str) -> List[ALPSSubsection]:
        """
        Parse Section 6 content into structured subsections using simple splitting.

        Args:
            section_content (str): Raw Section 6 content

        Returns:
            List[ALPSSubsection]: List of parsed subsections

        Raises:
            ALPSParseError: If subsections cannot be parsed
        """
        try:
            logger.info("Parsing subsections using simple splitting...")

            subsections: List[ALPSSubsection] = []
            # Split section content by subsection delimiter
            contents = section_content.split('\n### ')[1:]
            logger.info(f"Contents: {len(contents)}")

            for content in contents:
                content = content.strip()
                if not content:
                    continue

                try:
                    # Extract ALPSSubSection from content using LLM with structured output
                    system_prompt = """
You are an expert at analyzing ALPS document subsections. Extract structured information from the provided content.

Rules:
1. Extract the main title from the first line or heading
2. Look for user stories (typically starting with "As a...")
3. Extract technical details about implementation
4. Identify complexity level if mentioned
5. If any field is not found, use empty string or null
"""

                    human_prompt = f"""
Extract structured information from this subsection content:

{content}
"""
                    messages = [
                        SystemMessage(content=system_prompt),
                        HumanMessage(content=human_prompt)
                    ]

                    llm = self.llm.with_structured_output(ALPSSubsection)
                    response = await llm.ainvoke(messages)
                    logger.info(f"Response content: {response}")
                    subsections.append(response)
                except Exception as e:
                    logger.warning(f"Failed to parse subsection with LLM, using fallback: {str(e)}")

            logger.info(f"Successfully parsed {len(subsections)} subsections 🔍")
            return subsections

        except Exception as e:
            logger.error(f"Error parsing subsections: {traceback.format_exc()}")
            raise ALPSParseError(f"Failed to parse subsections: {str(e)}")

    async def parse_document(self, file_path: str) -> ALPSDocument:
        """
        Parse complete ALPS document and extract Section 6.

        Args:
            file_path (str): Path to the ALPS document

        Returns:
            ALPSDocument: Parsed ALPS document with Section 6 data

        Raises:
            ALPSParseError: If document cannot be parsed
        """
        try:
            logger.info(f"Starting ALPS document parsing: {file_path}")

            # Read document
            content = self.read_alps_document(file_path)
            logger.info(f"Read {len(content)} characters from {file_path}")

            # Extract Section 6
            section_6_content = await self.extract_section_6(content)
            logger.info(f"Section 6 content: {section_6_content}")

            # Parse subsections
            subsections = await self.parse_subsections(section_6_content)
            logger.info(f"Parsed {len(subsections)} subsections")

            return

            # Create Section 6 object
            section_6 = ALPSSection(
                section_number="6",
                section_title="Feature-Level Specification",
                content=section_6_content,
                subsections=subsections
            )

            # Create document metadata
            metadata = {
                "file_path": file_path,
                "total_characters": len(content),
                "section_6_characters": len(section_6_content),
                "subsections_count": len(subsections),
                "parsed_at": None  # Will be set by caller if needed
            }

            # Create ALPS document
            document = ALPSDocument(
                sections={"6": section_6},
                metadata=metadata
            )

            logger.info(f"Successfully parsed ALPS document with {len(subsections)} features 🎯")
            return document

        except ALPSParseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during document parsing: {traceback.format_exc()}")
            raise ALPSParseError(f"Unexpected error: {str(e)}")

    def validate_section_6(self, section: ALPSSection) -> Tuple[bool, List[str]]:
        """
        Validate extracted Section 6 for completeness and quality.

        Args:
            section (ALPSSection): Section 6 to validate

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_issues)
        """
        issues = []

        try:
            # Check if section has content
            if not section.content.strip():
                issues.append("Section 6 content is empty")

            # Check if subsections exist
            if not section.subsections:
                issues.append("No subsections found in Section 6")

            # Validate each subsection
            for subsection in section.subsections:
                if not subsection.subsection_number:
                    issues.append("Subsection missing number")

                if not subsection.subsection_title:
                    issues.append(f"Subsection {subsection.subsection_number} missing title")

                if not subsection.content.strip():
                    issues.append(f"Subsection {subsection.subsection_number} has empty content")

            # Check for duplicate subsection numbers
            numbers = [sub.subsection_number for sub in section.subsections]
            if len(numbers) != len(set(numbers)):
                issues.append("Duplicate subsection numbers found")

            is_valid = len(issues) == 0

            if is_valid:
                logger.info("Section 6 validation passed ✅")
            else:
                logger.warning(f"Section 6 validation found {len(issues)} issues")

            return is_valid, issues

        except Exception as e:
            logger.error(f"Error during validation: {traceback.format_exc()}")
            return False, [f"Validation error: {str(e)}"]


# Convenience function for direct usage
async def parse_alps_document(file_path: str) -> ALPSDocument:
    """
    Convenience function to parse an ALPS document.

    Args:
        file_path (str): Path to the ALPS document

    Returns:
        ALPSDocument: Parsed ALPS document

    Raises:
        ALPSParseError: If parsing fails
    """
    parser = ALPSParser()
    return await parser.parse_document(file_path)


# Example usage for testing
if __name__ == "__main__":
    async def main():
        """Example usage of the ALPS parser."""
        try:
            # Example file path
            file_path = "specs/ALPS Trail SPEC.md"

            # Parse document
            parser = ALPSParser()
            document = await parser.parse_document(file_path)

            # Display results
            print(f"Parsed document with {len(document.sections)} sections")
            if "6" in document.sections:
                section_6 = document.sections["6"]
                print(f"Section 6 has {len(section_6.subsections)} subsections")

                # Validate
                is_valid, issues = parser.validate_section_6(section_6)
                print(f"Validation: {'✅ Passed' if is_valid else '❌ Failed'}")
                if issues:
                    for issue in issues:
                        print(f"  - {issue}")

        except ALPSParseError as e:
            print(f"Parsing error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    # Run example
    asyncio.run(main())
