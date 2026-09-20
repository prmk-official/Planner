import streamlit as st
from datetime import date

from agent import process_input
from local_storage import get_all_items, save_items
from calendar_utils import create_ics


st.set_page_config(
    page_title="AI Planner",
    page_icon="📋",
    layout="wide",
)


def priority_rank(priority):
    return {
        "OVERDUE": 0,
        "URGENT": 1,
        "HIGH": 2,
        "MEDIUM": 3,
        "LOW": 4,
        None: 5,
    }.get(priority, 5)


def sorted_tasks(items):
    tasks = [
        item for item in items
        if item.get("type") == "TASK"
    ]

    return sorted(
        tasks,
        key=lambda item: (
            priority_rank(item.get("priority")),
            item.get("days_remaining", 999999),
            item.get("title", "").lower(),
        ),
    )


def sorted_events(items):
    events = [
        item for item in items
        if item.get("type") == "EVENT"
    ]

    return sorted(
        events,
        key=lambda item: (
            item.get("resolved_date") or "9999-12-31",
            item.get("time_text") or "99:99",
            item.get("title", "").lower(),
        ),
    )


def show_item(item):
    item_type = item.get("type")
    title = item.get("title", "Untitled")

    if item_type == "EVENT":
        st.markdown(f"**📅 {title}**")

        event_date = (
            item.get("resolved_date")
            or item.get("date_text")
            or "No date"
        )
        event_time = item.get("time_text") or "No time"

        st.caption(f"{event_date} • {event_time}")

    else:
        priority = item.get("priority") or "NO DEADLINE"
        st.markdown(f"**{title}**")
        st.caption(
            f"{priority} • "
            f"{item.get('resolved_date') or 'No deadline'}"
        )


st.title("📋 AI Planner")
st.write(
    "Turn messy student information into structured tasks, "
    "events, priorities, and actionable plans."
)

tab_plan, tab_saved, tab_calendar = st.tabs(
    ["Add & Plan", "Saved Planner", "Calendar"]
)

with tab_plan:
    st.subheader("Tell the planner what is happening")

    user_input = st.text_area(
        "Natural-language input",
        height=150,
        placeholder=(
            "I have a GDG meeting tomorrow at 4 PM. "
            "Submit my ML assignment by Monday. "
            "Bring my project report to the meeting."
        ),
    )

    if st.button("Extract & Save", type="primary"):
        if not user_input.strip():
            st.warning("Enter some information first.")
        else:
            with st.spinner("Understanding your input..."):
                try:
                    result = process_input(user_input)
                    saved_ids = save_items(result)

                    if not result.items:
                        st.info("No tasks or events were detected.")
                    else:
                        st.success(
                            f"Processed {len(saved_ids)} planner item(s)."
                        )

                        for item in result.items:
                            item_dict = item.model_dump()

                            if item.type.value == "EVENT":
                                with st.container(border=True):
                                    st.markdown(
                                        f"### 📅 {item.title}"
                                    )
                                    st.write(
                                        f"**Date:** "
                                        f"{item.resolved_date or item.date_text or 'No date'}"
                                    )
                                    st.write(
                                        f"**Time:** "
                                        f"{item.time_text or 'No time'}"
                                    )
                            else:
                                with st.container(border=True):
                                    st.markdown(
                                        f"### 📝 {item.title}"
                                    )
                                    st.write(
                                        f"**Priority:** "
                                        f"{item.priority or 'NO DEADLINE'}"
                                    )
                                    st.write(
                                        f"**Due:** "
                                        f"{item.resolved_date or 'No deadline'}"
                                    )

                except Exception as error:
                    st.error(
                        f"Could not process the input: "
                        f"{type(error).__name__}: {error}"
                    )

    st.divider()

    st.subheader("Plan My Day")

    saved_items = get_all_items()

    if not saved_items:
        st.info("Add some tasks or events first.")
    else:
        today = date.today().isoformat()

        today_tasks = [
            item
            for item in saved_items
            if (
                item.get("type") == "TASK"
                and item.get("resolved_date")
                and item.get("resolved_date") <= today
            )
        ]

        upcoming_tasks = sorted_tasks(saved_items)[:5]

        today_events = [
            item
            for item in sorted_events(saved_items)
            if item.get("resolved_date") == today
        ]

        st.markdown("#### What needs attention")

        if today_events:
            for event in today_events:
                show_item(event)

        if today_tasks:
            for task in sorted_tasks(today_tasks):
                show_item(task)

        if not today_events and not today_tasks:
            st.info("Nothing is due today.")

        st.markdown("#### Next priorities")

        for task in upcoming_tasks:
            show_item(task)

with tab_saved:
    st.subheader("Saved Planner")

    items = get_all_items()

    if not items:
        st.info("No saved items yet.")
    else:
        events = sorted_events(items)
        tasks = sorted_tasks(items)

        st.metric("Total items", len(items))

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📅 Events")
            if events:
                for event in events:
                    with st.container(border=True):
                        show_item(event)
            else:
                st.caption("No events.")

        with col2:
            st.markdown("### 📝 Tasks")
            if tasks:
                for task in tasks:
                    with st.container(border=True):
                        show_item(task)
            else:
                st.caption("No tasks.")

with tab_calendar:
    st.subheader("Calendar Export")

    items = get_all_items()
    calendar_events = [
        item
        for item in items
        if (
            item.get("type") == "EVENT"
            and item.get("resolved_date")
        )
    ]

    if not calendar_events:
        st.info(
            "No dated events are available for calendar export."
        )
    else:
        st.write(
            "Export your extracted events as an `.ics` calendar file."
        )

        for event in sorted_events(calendar_events):
            show_item(event)

        ics_content = create_ics(calendar_events)

        st.download_button(
            label="Download Calendar (.ics)",
            data=ics_content,
            file_name="ai_planner_events.ics",
            mime="text/calendar",
            type="primary",
        )
