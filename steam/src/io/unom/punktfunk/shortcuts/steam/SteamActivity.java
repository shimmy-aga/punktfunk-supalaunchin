package io.unom.punktfunk.shortcuts.steam;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Toast;

/**
 * Launcher tile that starts Steam Big Picture on the homelab host through the
 * official Punktfunk app. The link uses the host's private record id, so the
 * console UI dials it directly without the "Open this link?" prompt.
 */
public final class SteamActivity extends Activity {
    private static final String URL =
            "punktfunk://connect/f46c67d5-24f1-43b2-8e6c-27ebbb401854"
          + "?fp=2e123935076f66914368051920cea981792edf1f5a40ba4d9d489501d62004e5"
          + "&host=192.168.2.14&launch=steam%3Abig-picture";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(URL));
        intent.setPackage("io.unom.punktfunk");
        try {
            startActivity(intent);
        } catch (ActivityNotFoundException | SecurityException e) {
            Toast.makeText(this, "Punktfunk is not installed", Toast.LENGTH_LONG).show();
        }
        finish();
    }
}
