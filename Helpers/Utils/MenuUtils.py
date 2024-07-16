from Helpers.Utils.ApplicationVariables import ApplicationVariables


queue_video_path = ApplicationVariables().get("QUEUE_VIDEO_PATH")


def mount_menu_for_videos_to_convert(permitted_video_files_values, total):
    if total <= 0:
        raise IndexError(f"Directory {
                         queue_video_path} has no file to convert, put video file in it or download a video first.")

    print("all - To convert ALL files")
    print("back - Go back to main menu")
    for i in permitted_video_files_values:
        print(f"{i} - {permitted_video_files_values.get(i)}")
