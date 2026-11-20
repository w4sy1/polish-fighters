package io.github.openlf2.openlf2;

import static org.junit.Assert.*;
import java.util.List;
import java.util.Arrays;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.annotation.Config;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 34)
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

    @Test public void githubCatalogueRequiresTrustedSignatureAndReleaseUrls() throws Exception {
        org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters signer=
            new org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters(new java.security.SecureRandom());
        byte[] key=signer.generatePublicKey().getEncoded();
        String entry="{\"id\":\"lf4-turbo\",\"name\":\"LF4 Turbo\",\"version\":\"1.0.0\",\"profile\":\"lf_four_turbo\","
            +"\"url\":\"https://github.com/w4sy1/polish-fighters/releases/download/mods/lf4-turbo-1.0.0.zip\","
            +"\"sha256\":\""+"a".repeat(64)+"\",\"size_bytes\":10,\"unpacked_size_bytes\":20}";
        byte[] raw=("{\"channel\":\"stable\",\"format\":\"polish-fighters-mods\",\"packages\":["+entry+"],\"revision\":1}")
            .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        List<AndroidModSources.Package> rows=AndroidModSources.parseGitHubCatalogue(raw,sign(signer,raw),key);
        assertEquals(1,rows.size());
        assertEquals("LF4 Turbo",rows.get(0).name);
        assertEquals("lf_four_turbo",rows.get(0).profile);
        byte[] tampered=raw.clone();tampered[tampered.length-3]='2';
        try{AndroidModSources.parseGitHubCatalogue(tampered,sign(signer,raw),key);fail("accepted tampered catalogue");}catch(java.io.IOException expected){}
        byte[] evil=new String(raw,java.nio.charset.StandardCharsets.UTF_8).replace("github.com/w4sy1","github.com/evil1")
            .getBytes(java.nio.charset.StandardCharsets.UTF_8);
        try{AndroidModSources.parseGitHubCatalogue(evil,sign(signer,evil),key);fail("accepted foreign URL");}catch(java.io.IOException expected){}
        assertTrue(AndroidModSources.githubHost("https://release-assets.githubusercontent.com/x"));
        assertFalse(AndroidModSources.githubHost("https://evil.example/x"));
        assertFalse(AndroidModSources.githubHost("http://github.com/x"));
    }

    private static byte[] sign(org.bouncycastle.crypto.params.Ed25519PrivateKeyParameters key,byte[] data){
        org.bouncycastle.crypto.signers.Ed25519Signer signer=new org.bouncycastle.crypto.signers.Ed25519Signer();
        signer.init(true,key);signer.update(data,0,data.length);return signer.generateSignature();
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
