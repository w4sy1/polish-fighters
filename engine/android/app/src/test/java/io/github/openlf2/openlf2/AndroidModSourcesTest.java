package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import java.util.List;
import java.util.Arrays;
import org.junit.Test;

public class AndroidModSourcesTest {
    @Test public void scraperKeepsOnlyProjectPagesOnTheConfiguredHttpsHost() throws Exception {
        AndroidModSources.Source source=AndroidModSources.SOURCES.get(2);
        String html="<a href='/mods/top'>popular</a><a href='/mods/add'>add mod</a>"
            +"<a href='/mods/dragonball-super-edition'>DragonBall Super Edition</a>"
            +"<a href='http://www.moddb.com/mods/insecure'>insecure</a>"
            +"<a href='https://evil.example/mods/other'>external</a>";
        List<AndroidModSources.Candidate> rows=AndroidModSources.parsePage(source,html);
        assertEquals(1,rows.size());
        assertEquals("DragonBall Super Edition",rows.get(0).label);
        assertEquals("https://www.moddb.com/mods/dragonball-super-edition",rows.get(0).url);
    }

    @Test public void robotsRulesHonorSpecificAllowAndWildcardDisallow() {
        List<AndroidModSources.RobotsRule> rules=Arrays.asList(
            new AndroidModSources.RobotsRule(false,"/lfe-fileplanet/*"),
            new AndroidModSources.RobotsRule(true,"/lfe-fileplanet/versions/"));
        assertTrue(AndroidModSources.robotsAllowed("/lfe-fileplanet/versions/12",rules));
        assertFalse(AndroidModSources.robotsAllowed("/lfe-fileplanet/mods",rules));
        assertTrue(AndroidModSources.robotsAllowed("/public/",rules));
    }
}
