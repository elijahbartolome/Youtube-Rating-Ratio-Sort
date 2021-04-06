# Youtube-Rating-Ratio-Sort-Chrome-Extension

To run, execute "py best_ratios.py" in folder

Given a Youtube URL as input, best_ratios will give a list of the best, relevant videos in order from ratings ratio descending. 

Ratings Ratio is defined as the number of likes divided by number of dislikes. In the chance that there is no dislikes, the ratio is simply just the number of likes (this is to avoid a division by zero error).

Supported URLs can come from search queries, playlists, channels, and a video itself.
