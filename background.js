chrome.tabs.query({currentWindow: true, active: true}, function(tabs){
    var myurl = tabs[0].url;
    console.log(tabs[0].url);
    System.Diagnostics.Process.Start("python.exe", "file.py");
});
